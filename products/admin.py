from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, Product, Order, OrderItem, Cart, Category

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('e-BudolKa User Details', {
            'fields': ('role',),
            'classes': ('collapse',),
        }),
    )

# Address Admin
class AddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'full_address', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'full_address')

# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

# Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

# Order Admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)

# OrderItem Admin
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'price', 'quantity')
    list_filter = ('order__created_at',)
    search_fields = ('product__name',)

# Cart Admin
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user__username',)

# Register all models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Cart, CartAdmin)
