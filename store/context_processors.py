from .models import Category, Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist

# 1. Ye hai wo function jo missing tha (Categories dikhane ke liye)
def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)

# 2. Ye hai tera Cart Counter (Jo Cart ka number dikhata hai)
def counter(request):
    cart_count = 0
    
    # Admin panel me count dikhane ki zarurat nahi
    if 'admin' in request.path:
        return {}

    try:
        cart = None
        cart_items = None
        
        # LOGIC 1: Agar User Login Hai
        if request.user.is_authenticated:
            # Seedha User ke items filter karo
            cart_items = CartItem.objects.filter(user=request.user)
        
        # LOGIC 2: Agar User Guest (Bina Login) Hai
        else:
            try:
                # Session ID se Cart dhoondo
                # Note: Hum views se import nahi kar rahe taaki error na aaye
                session_id = request.session.session_key
                if not session_id:
                    session_id = request.session.create()
                
                cart = Cart.objects.filter(cart_id=session_id).first()
                if cart:
                    cart_items = CartItem.objects.filter(cart=cart)
                else:
                    cart_items = []
            except:
                cart_items = []
        
        # Total Quantity count karo
        if cart_items:
            for cart_item in cart_items:
                cart_count += cart_item.quantity
                
    except Exception as e:
        cart_count = 0
        
    return dict(cart_count=cart_count)