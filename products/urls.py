from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'), 
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/update/<int:id>/<str:action>/', views.update_cart, name='update_cart'),
    
    path('api/products/', views.ProductListAPI.as_view(), name='api_product_list'),
    path('api/products/<int:pk>/', views.ProductDetailAPI.as_view(), name='api_product_detail'),

    path('seller/login/', auth_views.LoginView.as_view(
        template_name='products/seller_login.html', 
        next_page='seller_dashboard'
    ), name='seller_login'),
    
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/add/', views.add_product, name='add_product'), 
    path('seller/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('seller/remove/<int:id>/', views.remove_product, name='remove_product'),

    path('my-orders/', views.my_orders, name='my_orders'),
    path('checkout/', views.checkout, name='checkout'),

    # Admin URLs
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin/products/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin/categories/create/', views.admin_category_create, name='admin_category_create'),
    path('admin/categories/edit/<int:category_id>/', views.admin_category_edit, name='admin_category_edit'),
    path('admin/categories/delete/<int:category_id>/', views.admin_category_delete, name='admin_category_delete'),
]

