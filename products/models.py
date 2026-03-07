from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    image = models.ImageField(upload_to='product_images/', blank=True, null=True)

    image_url = models.URLField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Address(models.Model):
    name = models.CharField(max_length=50, help_text="e.g., Home, Office, Dorm")
    full_address = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.full_address}"