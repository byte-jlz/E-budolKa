from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_product, name='add_product'),
    path('', views.product_list, name='product_list'),
  
    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    
    path('edit/<int:id>/', views.edit_product, name='edit_product'),
    path('remove/<int:id>/', views.remove_product, name='remove_product'),

    path('cart/add/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),

    path('cart/update/<int:id>/<str:action>/', views.update_cart, name='update_cart'),

    path('api/products/', views.ProductListAPI.as_view(), name='api_product_list'),
    path('api/products/<int:pk>/', views.ProductDetailAPI.as_view(), name='api_product_detail'),
    
]