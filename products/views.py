from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.core.paginator import Paginator
from rest_framework import generics
from .models import Product, Order, OrderItem, Address, Cart, CustomUser, Category
from .forms import ProductForm, CustomUserCreationForm
from .serializers import ProductSerializer

def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

def is_seller(user):
    return user.is_authenticated

# API Views
class ProductListAPI(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# Main Views
def product_list(request):
    categories = Category.objects.all()
    selected_category = request.GET.get('category')
    search_query = request.GET.get('search', '')
    
    products = Product.objects.all()
    
    # Filter by category if selected
    if selected_category:
        products = products.filter(category__slug=selected_category)
    
    # Search functionality
    if search_query:
        products = products.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(category__name__icontains=search_query)
        )
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
    }
    return render(request, 'products/product_list.html', context)

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is in stock
    if product.stock <= 0:
        messages.error(request, f"Sorry, {product.name} is completely out of stock.")
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_data = cart.cart_data 
    product_id_str = str(product_id) 
    
    # Check current cart quantity vs available stock
    current_quantity = cart_data.get(product_id_str, 0)
    
    if current_quantity < product.stock:
        cart_data[product_id_str] = current_quantity + 1
        messages.success(request, f"{product.name} added to your cart!")
    else:
        messages.error(request, f"Maximum stock reached for {product.name}.")
        
    cart.cart_data = cart_data
    cart.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))

@login_required
def update_cart(request, id, action):
    cart = get_object_or_404(Cart, user=request.user)
    cart_data = cart.cart_data
    product_id_str = str(id)
    product = get_object_or_404(Product, id=id)

    if product_id_str in cart_data:
        if action == 'add':
            if cart_data[product_id_str] < product.stock:
                cart_data[product_id_str] += 1
        elif action == 'minus':
            if cart_data[product_id_str] > 1:
                cart_data[product_id_str] -= 1
            elif cart_data[product_id_str] == 1:
                del cart_data[product_id_str]
        elif action == 'remove_all':
            del cart_data[product_id_str]
        
        cart.cart_data = cart_data
        cart.save()
    
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_data = cart.cart_data
    
    cart_items = []
    grand_total = 0
    
    for product_id_str, quantity in cart_data.items():
        product = Product.objects.get(id=int(product_id_str))
        total_price = product.price * quantity
        grand_total += total_price
        
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price
        })
    
    addresses = Address.objects.filter(user=request.user)
    
    context = {
        'cart_items': cart_items,
        'grand_total': grand_total,
        'addresses': addresses,
    }
    return render(request, 'products/cart.html', context)

@login_required
def checkout(request):
    if request.method == 'POST':
        address_id = request.POST.get('address')
        if not address_id:
            messages.error(request, "Please select a delivery address.")
            return redirect('view_cart')

        cart = get_object_or_404(Cart, user=request.user)
        cart_data = cart.cart_data

        if not cart_data:
            messages.error(request, "Your cart is empty.")
            return redirect('view_cart')

        try:
            with transaction.atomic():
                address = get_object_or_404(Address, id=address_id, user=request.user)
                
                total_amount = 0
                for product_id_str, quantity in cart_data.items():
                    product = Product.objects.get(id=int(product_id_str))
                    total_amount += product.price * quantity

                order = Order.objects.create(
                    user=request.user,
                    address=address,
                    total_amount=total_amount,
                    payment_status='Pending', 
                    status='Processing'
                )

                for product_id_str, quantity in cart_data.items():
                    product = Product.objects.get(id=int(product_id_str))
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=product.price,
                        quantity=quantity
                    )
                
                # Clear cart after successful order
                cart.cart_data = {}
                cart.save()
                
                messages.success(request, "Order placed successfully!")
                return redirect('my_orders')
                
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('view_cart')
    
    return redirect('view_cart')

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'products/my_orders.html', {'orders': orders})

# Seller Views
def seller_login(request):
    return render(request, 'products/seller_login.html')

def seller_dashboard(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'products/seller_dashboard.html', {'products': products})

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save() 
            return redirect('seller_dashboard')
    else:
        form = ProductForm()
    return render(request, 'products/add_product.html', {'form': form})

def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('seller_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/edit_product.html', {'form': form, 'product': product})

def remove_product(request, id):
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        product.delete()
        return redirect('seller_dashboard')
        
    return render(request, 'products/remove_product.html', {'product': product})

# User Registration
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            CustomUser.objects.create(
                username=user.username,
                email=user.email,
                role='Customer'
            )
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'products/signup.html', {'form': form})

# Admin Views
@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_users = CustomUser.objects.count()
    total_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    recent_products = Product.objects.all().order_by('-created_at')[:5]

    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'recent_products': recent_products,
    }
    return render(request, 'products/admin/dashboard.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(category__name__icontains=search_query)
        )
    
    # Filter by availability
    filter_stock = request.GET.get('stock', '')
    if filter_stock == 'in_stock':
        products = products.filter(stock__gt=0)
    elif filter_stock == 'out_of_stock':
        products = products.filter(stock=0)
    
    # Filter by category
    filter_category = request.GET.get('category', '')
    if filter_category:
        products = products.filter(category__id=filter_category)
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'filter_stock': filter_stock,
        'filter_category': filter_category,
    }
    return render(request, 'products/admin/products.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm() 
    
    context = {
        'form': form,
    }
    return render(request, 'products/admin/product_add.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'products/admin/product_edit.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('admin_products')
    
    context = {
        'product': product,
    }
    return render(request, 'products/admin/product_delete.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status
    filter_status = request.GET.get('status', '')
    if filter_status:
        orders = orders.filter(status=filter_status)
    
    # Filter by payment status
    filter_payment = request.GET.get('payment', '')
    if filter_payment:
        orders = orders.filter(payment_status=filter_payment)
    
    context = {
        'orders': orders,
        'filter_status': filter_status,
        'filter_payment': filter_payment,
        'status_choices': Order.objects.values_list('status', flat=True).distinct(),
        'payment_choices': Order.objects.values_list('payment_status', flat=True).distinct(),
        'total_revenue': sum(order.total_amount for order in orders),
        'processing_count': orders.filter(status='Processing').count(),
        'delivered_count': orders.filter(status='Delivered').count(),
    }
    return render(request, 'products/admin/orders.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    # Handle status update form submission
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_payment_status = request.POST.get('payment_status')
        
        if new_status:
            order.status = new_status
        if new_payment_status:
            order.payment_status = new_payment_status
            
        order.save()
        messages.success(request, 'Order status updated successfully!')
        return redirect('admin_order_detail', order_id=order_id)
    
    # Define status choices
    STATUS_CHOICES = ['Processing', 'Shipped', 'Delivered', 'Cancelled']
    PAYMENT_CHOICES = ['Pending', 'Paid', 'Failed', 'Refunded']
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_choices': STATUS_CHOICES,
        'payment_choices': PAYMENT_CHOICES,
    }
    return render(request, 'products/admin/order_detail.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_users(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )
    
    # Filter by role
    filter_role = request.GET.get('role', '')
    if filter_role:
        users = users.filter(role=filter_role)
    
    context = {
        'users': users,
        'search_query': search_query,
        'filter_role': filter_role,
        'role_choices': CustomUser.ROLE_CHOICES,
        'admin_count': users.filter(role='Admin').count(),
        'active_count': users.filter(is_active=True).count(),
    }
    return render(request, 'products/admin/users.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user_orders = Order.objects.filter(user=user).order_by('-created_at')
    user_addresses = Address.objects.filter(user=user)
    
    # Handle role update form submission
    if request.method == 'POST' and 'role' in request.POST:
        new_role = request.POST.get('role')
        if new_role:
            user.role = new_role
            user.save()
            messages.success(request, f'User role updated to {new_role} successfully!')
            return redirect('admin_user_detail', user_id=user_id)
    
    # Get user cart if exists
    user_cart = Cart.objects.filter(user=user).first()
    
    context = {
        'user': user,
        'user_orders': user_orders,
        'user_addresses': user_addresses,
        'user_cart': user_cart,
        'role_choices': CustomUser.ROLE_CHOICES,
    }
    return render(request, 'products/admin/user_detail.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('admin_users')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'products/admin/user_create.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_user_delete(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('admin_users')
    
    context = {
        'user': user,
    }
    return render(request, 'products/admin/user_delete.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_categories(request):
    categories = Category.objects.all().order_by('name')
    total_products = Product.objects.count()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    context = {
        'categories': categories,
        'search_query': search_query,
        'total_products': total_products,
    }
    return render(request, 'products/admin/categories.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category = Category.objects.create(name=name)
            messages.success(request, 'Category created successfully!')
            return redirect('admin_categories')
        else:
            messages.error(request, 'Category name is required!')
    
    return render(request, 'products/admin/category_create.html')

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category.name = name
            category.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('admin_categories')
        else:
            messages.error(request, 'Category name is required!')
    
    context = {
        'category': category,
    }
    return render(request, 'products/admin/category_edit.html', context)

@login_required(login_url='/login/')
@user_passes_test(is_admin, login_url='/login/')
def admin_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    product_count = category.products.count()
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('admin_categories')
    
    context = {
        'category': category,
        'product_count': product_count,
    }
    return render(request, 'products/admin/category_delete.html', context)
