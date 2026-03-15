from django.contrib import admin
from .models import Product, Address, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 
    readonly_fields = ['product', 'price', 'quantity']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'payment_method', 'created_at']
    list_filter = ['created_at', 'payment_method']
    inlines = [OrderItemInline]

admin.site.register(Product)
admin.site.register(Address)
admin.site.register(Order, OrderAdmin)