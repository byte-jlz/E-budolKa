from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from django.contrib import messages
from .models import Product, Order, OrderItem, Address, Cart
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


@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # 1. Immediate check: Is the product completely sold out?
    if product.stock <= 0:
        messages.error(request, f"Sorry, {product.name} is completely out of stock.")
        # Send them back to where they came from
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_data = cart.cart_data 
    product_id_str = str(product_id) 
    
    # 2. Check current cart quantity vs available stock
    current_quantity = cart_data.get(product_id_str, 0)
    
    if current_quantity < product.stock:
        cart_data[product_id_str] = current_quantity + 1
        messages.success(request, f"{product.name} added to your cart!")
    else:
        messages.error(request, f"Maximum stock reached for {product.name}.")
        
    cart.cart_data = cart_data
    cart.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required(login_url='/login/')
def update_cart(request, id, action):
    # 1. Fetch the user's cart straight from the database
    cart = get_object_or_404(Cart, user=request.user)
    cart_data = cart.cart_data
    product_id_str = str(id)
    
    # 2. Fetch the product to check stock limits
    product = get_object_or_404(Product, id=id)

    # 3. Modify the JSON data based on the button clicked
    if product_id_str in cart_data:
        if action == 'add':
            if cart_data[product_id_str] < product.stock:
                cart_data[product_id_str] += 1
            else:
                messages.error(request, f'Maximum stock reached for {product.name}.')
        elif action == 'minus':
            cart_data[product_id_str] -= 1
            if cart_data[product_id_str] <= 0:
                del cart_data[product_id_str] # Removes item if it hits 0
        elif action == 'remove_all':
            del cart_data[product_id_str]

    # 4. Save the updated JSON back to the database!
    cart.cart_data = cart_data
    cart.save()
    
    return redirect('view_cart')

@login_required(login_url='/login/')
def view_cart(request):
    # 1. Get the user's cart from the database
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_data = cart.cart_data
    
    # 2. Prepare empty lists and totals for the frontend
    cart_items = []
    grand_total = 0
    
    # 3. Loop through the JSON data and pull the real products
    for product_id_str, quantity in cart_data.items():
        try:
            # Fetch the actual product from the DB using the ID
            product = Product.objects.get(id=int(product_id_str))
            total_item_price = product.price * quantity
            grand_total += total_item_price
            
            # Add it to our list for the HTML template
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': total_item_price,
            })
        except Product.DoesNotExist:
            # Just in case a product was deleted from the store while in the cart
            pass 

    # 4. Send the data to your HTML page
    context = {
        'cart_items': cart_items,
        'grand_total': grand_total,
    }
    
    # Make sure to change 'cart.html' to whatever your actual template file is named!
    return render(request, 'products/cart.html', context)



@login_required(login_url='/login/')
def my_orders(request):
    # Fetch orders for this specific user, ordered by newest first (-created_at)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'products/my_orders.html', {'orders': orders})
