from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'), 
    path('cart/add/<int:id>/', views.add_to_cart, name='add_to_cart'),
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
]