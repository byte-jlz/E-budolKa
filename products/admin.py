from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, Product, Order, OrderItem, Cart

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('e-BudolKa User Details', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('e-BudolKa User Details', {'fields': ('email', 'role')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')

# Register all 5 models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Address)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Cart)