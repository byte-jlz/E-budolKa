from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# 1. Custom User Model (Address removed from here)
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    ROLE_CHOICES = [
        ('Customer', 'Customer'),
        ('Admin', 'Admin'),
    ]
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='Customer')

    def __str__(self):
        return self.username

# 2. Address Model (Brought back for multiple addresses!)
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=50, help_text="e.g., Home, Office, Dorm")
    full_address = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.full_address}"

# 3. Product Model
class Product(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# 4. Order Model
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    
    payment_status = models.CharField(max_length=50, default='Pending')
    status = models.CharField(max_length=50, default='Processing')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

# 5. OrderItem Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order #{self.order.id})"