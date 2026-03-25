from .models import Cart

def cart_count(request):
    count = 0
    # Only try to fetch the cart if the user is actually logged in
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            # This adds up all the quantities inside your JSON data!
            count = sum(cart.cart_data.values())
        except Cart.DoesNotExist:
            count = 0
            
    # This makes the variable 'cart_item_count' available to ALL your HTML files
    return {'cart_item_count': count}