from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from django.contrib import messages
from .models import Product, Address, Order, OrderItem # <-- Ensure Order and OrderItem are here!
from rest_framework import generics
from .serializers import ProductSerializer
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required

def is_seller(user):
    return user.is_staff

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = UserCreationForm()
        
    return render(request, 'products/register.html', {'form': form})

class ProductListAPI(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

def product_list(request):
    products = Product.objects.all()  # Fetches all products from the database
    return render(request, 'products/product_list.html', {'products': products})

@user_passes_test(is_seller, login_url='/seller/login/')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() 
            return redirect('add_product')
    else:
        form = ProductForm() # Shows an empty form

    return render(request, 'products/add_product.html', {'form': form})

@user_passes_test(is_seller, login_url='/seller/login/')
def seller_dashboard(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'products/seller_dashboard.html', {'products': products})


@user_passes_test(is_seller, login_url='/seller/login/')
def edit_product(request, id):
    product = get_object_or_404(Product, id=id) # Find the exact product
    
    if request.method == 'POST':
        # The 'instance=product' tells Django to UPDATE, not create a new one!
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('seller_dashboard')
    else:
        # Pre-fill the form with the existing product data
        form = ProductForm(instance=product) 

    return render(request, 'products/edit_product.html', {'form': form, 'product': product})

@user_passes_test(is_seller, login_url='/seller/login/')
def remove_product(request, id):
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        product.delete() # Deletes it from the database
        return redirect('seller_dashboard')
        
    return render(request, 'products/remove_product.html', {'product': product})


def add_to_cart(request, id):
    cart = request.session.get('cart', {})
    
    product_id = str(id) # Session keys must be strings!

    product = get_object_or_404(Product, id=id)
    current_quantity = cart.get(product_id, 0)

    if current_quantity < product.stock:
        cart[product_id] = current_quantity + 1
        messages.success(request, f'Added {product.name} to your cart.')
    else:
        # Trigger an error message if they try to buy too many
        messages.error(request, f'Sorry, only {product.stock} available in stock!')

    request.session['cart'] = cart
    return redirect('product_list')

def update_cart(request, id, action):
    cart = request.session.get('cart', {})
    product_id = str(id)
    
    # Fetch the product here as well
    product = get_object_or_404(Product, id=id)

    if product_id in cart:
        if action == 'add':
            # Check stock before allowing the Plus button to work!
            if cart[product_id] < product.stock:
                cart[product_id] += 1
            else:
                messages.error(request, f'Maximum stock reached for {product.name}.')
        elif action == 'minus':
            cart[product_id] -= 1
            if cart[product_id] <= 0:
                del cart[product_id]
        elif action == 'remove_all':
            del cart[product_id]

    request.session['cart'] = cart
    return redirect('view_cart')


@login_required(login_url='/login/')
def view_cart(request):
    cart = request.session.get('cart', {})

    # 1. Calculate the totals
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            total = product.price * quantity
            total_price += total
            cart_items.append({'product': product, 'quantity': quantity, 'total': total})
        except Product.DoesNotExist:
            continue # If a product was deleted from the database, ignore it in the cart

    # 2. HANDLE THE CHECKOUT SUBMISSION
    if request.method == 'POST':
        address_id = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        
        # Failsafe: Ensure an address was selected
        if not address_id:
            messages.error(request, "Please select a delivery address.")
            return redirect('view_cart')

        address = get_object_or_404(Address, id=address_id)

        # Create the Master Receipt
        order = Order.objects.create(
            user=request.user,
            address=address,
            payment_method=payment_method,
            total_amount=total_price
        )

        # Create the specific products attached to the receipt
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['product'].price,
                quantity=item['quantity']
            )
            
            # Deduct the stock
            item['product'].stock -= item['quantity']
            if item['product'].stock < 0:
                item['product'].stock = 0
            item['product'].save()

        # Clear the cart and redirect
        request.session['cart'] = {}
        messages.success(request, 'Order successfully placed! Thank you for your purchase.')
        return redirect('product_list')


    # 3. HANDLE THE NORMAL CART PAGE LOAD
    # THIS FIXES THE DROPDOWN LEAK: It strictly filters by the currently logged-in user!
    addresses = Address.objects.filter(user=request.user)

    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'addresses': addresses
    })


def update_cart(request, id, action):
    cart = request.session.get('cart', {})
    product_id = str(id)

    if product_id in cart:
        if action == 'add':
            cart[product_id] += 1
        elif action == 'minus':
            cart[product_id] -= 1
            if cart[product_id] <= 0:
                del cart[product_id]
        elif action == 'remove_all':
            del cart[product_id]

    # Save the updated cart back to the session
    request.session['cart'] = cart
    return redirect('view_cart')

@login_required(login_url='/login/')
def my_orders(request):
    # Fetch orders for this specific user, ordered by newest first (-created_at)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'products/my_orders.html', {'orders': orders})
