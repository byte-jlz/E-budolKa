from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from .models import Product
from django.contrib import messages
from .models import Product, Address
from rest_framework import generics
from .serializers import ProductSerializer
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

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

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() 
            return redirect('add_product')
    else:
        form = ProductForm() # Shows an empty form

    return render(request, 'products/add_product.html', {'form': form})

def seller_dashboard(request):
    # This fetches all products, ordered by the newest first
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'products/seller_dashboard.html', {'products': products})


# 1. THE EDIT VIEW
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

# 2. THE REMOVE VIEW
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

# 2. VIEW CART PAGE
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    # Loop through the session cart and fetch the actual product data from the database
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        total = product.price * quantity
        total_price += total
        
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': total
        })
        
    return render(request, 'products/cart.html', {'cart_items': cart_items, 'total_price': total_price})


def view_cart(request):
    cart = request.session.get('cart', {})

    # 1. HANDLE THE CHECKOUT SUBMISSION
    if request.method == 'POST':
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, id=product_id)
            # Deduct the stock
            product.stock -= quantity 
            if product.stock < 0:
                product.stock = 0 # Prevent negative stock
            product.save()

        # Clear the session cart
        request.session['cart'] = {}

        # Trigger the pop-out confirmation message
        messages.success(request, 'Payment Successful! Your stock has been updated.')
        return redirect('view_cart')
    
    cart_items = []
    total_price = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        total = product.price * quantity
        total_price += total
        cart_items.append({'product': product, 'quantity': quantity, 'total': total})
    
    addresses = Address.objects.all()

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


