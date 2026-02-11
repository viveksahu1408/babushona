from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Cart, CartItem, ProductVariant
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegistrationForm,User # Ye ensure karna ki import ho
from django.contrib.auth.models import User  # <--- Ye line add karo
from django.contrib.auth.decorators import login_required
from django.db.models import Q
# store/views.py me models import wali line dhundo aur update karo:
from .models import Product, Category, Cart, CartItem, ProductVariant, Order, OrderProduct,Color,Size
#dashboard 
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
import datetime
from .forms import ProductForm, ProductVariantForm # <--- Ye update karo
from django.utils.text import slugify
from .forms import CategoryForm, SizeForm, ColorForm # Forms import update karo
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.mail import send_mail
from .models import ReviewRating,UserProfile
from .forms import UserForm, UserProfileForm,ReviewForm 
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


def home(request):
    # Sirf active products hi dikhayenge
    products = Product.objects.filter(is_active=True)
    return render(request, 'store/index.html', {'products': products})

def product_detail(request, slug):
    # 1. Product dhoondo (Slug ke through)
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # 2. Is product ke sare variants (Size/Color) nikalo
    variants = product.variants.all()
    
    # 3. Reviews fetch karo (Jo Status=True ho)
    reviews = ReviewRating.objects.filter(product=product, status=True)

    context = {
        'product': product,
        'variants': variants,
        'reviews': reviews,
    }
    return render(request, 'store/product_detail.html', context)


# 1. Helper function: User ki Session ID nikalne ke liye
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# ... (Home aur Product Detail wale functions wahi rahenge) ...

# store/views.py (UPDATED)

def add_cart(request, product_id):
    current_user = request.user
    
    # 1. Variant Data nikalo (Form se)
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1)) # Default 1
        
        # Variant object nikalo
        product_variant = get_object_or_404(ProductVariant, id=variant_id)

        # --- LOGIC START ---
        
        # CASE 1: Agar User Login hai (Database me User ID save karo)
        if current_user.is_authenticated:
            try:
                # Check karo kya ye variant pehle se cart me hai?
                cart_item = CartItem.objects.get(product_variant=product_variant, user=current_user)
                cart_item.quantity += quantity
                cart_item.save()
            except CartItem.DoesNotExist:
                # Agar nahi hai to naya banao
                cart_item = CartItem.objects.create(
                    product_variant=product_variant,
                    quantity=quantity,
                    user=current_user,  # <--- IMPORTANT: User save kar rahe hain
                    cart=None # User hai to Cart session ki zarurat nahi (ya null rakh sakte ho)
                )
                cart_item.save()
        
        # CASE 2: Agar User Guest hai (Session ID use karo)
        else:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id=_cart_id(request))
                cart.save()

            try:
                cart_item = CartItem.objects.get(product_variant=product_variant, cart=cart)
                cart_item.quantity += quantity
                cart_item.save()
            except CartItem.DoesNotExist:
                cart_item = CartItem.objects.create(
                    product_variant=product_variant,
                    quantity=quantity,
                    cart=cart, # <--- Guest ke liye Session Cart ID
                )
                cart_item.save()
        
    return redirect('cart')

# Cart page par (+) dabane ke liye
def add_qty_cart(request, cart_item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=cart)

    cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')

# Cart page par (-) dabane ke liye
def remove_cart(request, cart_item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=cart)

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

# Cart page par DELETE button ke liye
def remove_cart_item(request, cart_item_id):
    if request.user.is_authenticated:
        # Agar User Login hai to User ID se dhoondo
        cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    else:
        # Agar Guest hai to Cart Session se dhoondo
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=cart)

    cart_item.delete()
    return redirect('cart')

# 3. Cart Page Logic
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        shipping_charge = 0  # <--- Naya Variable
        
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product_variant.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        
        # --- SHIPPING LOGIC START ---
        if total < 500:
            shipping_charge = 50
        else:
            shipping_charge = 0
        # --- SHIPPING LOGIC END ---

        tax = (2 * total) / 100
        grand_total = total + tax + shipping_charge # Grand total me shipping jod diya

    except ObjectDoesNotExist:
        pass # Just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'shipping_charge': shipping_charge, # <--- Template ko bhejna hai
    }
    return render(request, 'store/cart.html', context)


#checkout code 
@login_required(login_url='handle_login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        shipping_charge = 0 # <--- Naya Variable
        
        # User login hai, to seedha User ke items nikalo
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        
        for cart_item in cart_items:
            total += (cart_item.product_variant.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        
        # --- SHIPPING LOGIC (Cart jaisa same) ---
        if total < 500:
            shipping_charge = 50
        else:
            shipping_charge = 0
        # ----------------------------------------

        tax = (2 * total) / 100
        grand_total = total + tax + shipping_charge
        
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'shipping_charge': shipping_charge, # <--- Template ko bhejna zaruri hai
    }
    return render(request, 'store/checkout.html', context)

def place_order(request, total=0, quantity=0):
    if request.method == 'POST':
        # 1. Cart Items Nikalo
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        cart_count = cart_items.count()
        
        if cart_count <= 0:
            return redirect('store')

        # 2. Total Calculation
        grand_total = 0
        tax = 0
        total = 0
        shipping_charge = 0
        
        for item in cart_items:
            total += (item.product_variant.product.price * item.quantity)
        
        # Shipping Rule
        if total < 500:
            shipping_charge = 50
        else:
            shipping_charge = 0

        tax = (2 * total) / 100
        grand_total = total + tax + shipping_charge
        
        
        # 3. Order Save Karna
        form = OrderForm(request.POST)
        
        if form.is_valid():
            data = Order()
            data.user = request.user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            
            # Ye field humne form me add ki thi
            data.payment_phone = form.cleaned_data['payment_phone']            
            
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.pin_code = form.cleaned_data['pin_code']
            
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save() # Pehli baar save (ID mil gayi)

            # 4. Generate Order Number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            
            # Order Number = Date + Order ID
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save() # Update with Order Number
            
            # 5. Move Cart Items to Order Product Table
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = data.id
                order_product.user_id = request.user.id
                order_product.product_variant = item.product_variant
                order_product.quantity = item.quantity
                order_product.product_price = item.product_variant.product.price
                order_product.ordered = True
                order_product.save()

                # 👇 STOCK KAM KARNE KA LOGIC (Loop ke andar) 👇
                
                # Variant ko pakdo
                variant = item.product_variant
                
                # Stock minus karo
                # (Make sure tere model me field ka naam 'stock' hai ya 'stock_quantity')
                variant.stock -= item.quantity  
                
                # Save kar do
                variant.save()
                
                # 👆 YAHAN KHATAM (Loop ke andar hi rehna chahiye) 👆

            # 6. Clear Cart
            CartItem.objects.filter(user=request.user).delete()
            
            # 7. Final Confirm
            data.is_ordered = True
            data.save()

            # 8. Success Page
            return render(request, 'store/order_complete.html', {'order': data})
            
        else:
            print("❌ FORM ERROR AAYA HAI:", form.errors)
            return redirect('checkout')
    else:
        return redirect('store')
    
    
# order track karne ke liye h 

def track_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        phone = request.POST.get('phone')
        
        try:
            # Order dhundne ke liye ID aur Phone dono match hona chahiye (Security ke liye)
            order = Order.objects.get(id=order_id, phone=phone)
            
            # Status Logic for Progress Bar
            status_percentage = 20
            if order.status == 'Accepted':
                status_percentage = 40
            elif order.status == 'Shipped':
                status_percentage = 70
            elif order.status == 'Completed':
                status_percentage = 100
            elif order.status == 'Cancelled':
                status_percentage = 0

            context = {
                'order': order,
                'found': True,
                'status_percentage': status_percentage
            }
            return render(request, 'store/track_order.html', context)
            
        except Order.DoesNotExist:
            return render(request, 'store/track_order.html', {'error': 'Order ID or Phone Number is incorrect.'})
            
    return render(request, 'store/track_order.html')        

#login signup code logic
def handle_register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # User create karna
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            messages.success(request, 'Registration successful. Please Login.')
            return redirect('handle_login')
    else:
        form = RegistrationForm()
        
    return render(request, 'store/register.html', {'form': form})

def handle_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(email=email, password=password) # Hum username ki jagah email use kar rahe hain
        if user is None:
            # Fallback: Django default username se check karta hai, humne username=email set kiya tha
            user = authenticate(username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials')
            
    return render(request, 'store/login.html')

def handle_logout(request):
    logout(request)
    return redirect('handle_login')

#user's dashboard show 

@login_required(login_url='handle_login')
def dashboard(request):
    # User ke email se match hone wale sare orders nikalo
    orders = Order.objects.order_by('-created_at').filter(email=request.user.email, is_ordered=True)
    
    order_count = orders.count()
    
    context = {
        'orders': orders,
        'order_count': order_count,
        
    }
    return render(request, 'store/dashboard.html', context)


#this is search and filter code concept
def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        # Case 1: Agar Category select ki gayi hai (e.g., /store/men/)
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_active=True)
        product_count = products.count()
    else:
        # Case 2: Normal Store Page (Sab dikhao)
        products = Product.objects.all().filter(is_active=True).order_by('id')
        product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)

def search(request):
    # Case 3: Search Bar logic
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            # Name YA Description me dhundo (Q object use hota hai 'OR' logic ke liye)
            products = Product.objects.order_by('-created_at').filter(Q(description__icontains=keyword) | Q(name__icontains=keyword))
            product_count = products.count()
    
    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


#dashboard code logic 
# Check: Sirf Superuser hi andar aa sake
def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    # 1. Total Stats
    orders = Order.objects.filter(is_ordered=True).order_by('-created_at')
    total_orders = orders.count()
    completed_orders = orders.filter(status='Completed').count()
    pending_orders = orders.filter(status='New').count()
    
    # Total Revenue (Kamai)
    total_revenue = Order.objects.filter(is_ordered=True).aggregate(Sum('order_total'))['order_total__sum']
    if total_revenue is None:
        total_revenue = 0

    # 2. Recent 5 Orders (Table ke liye)
    recent_orders = orders[:5]

    context = {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    return render(request, 'store/custom_admin/dashboard.html', context)

@user_passes_test(is_admin)
def admin_order_list(request):
    # Sare orders dekhne aur status badalne ke liye
    orders = Order.objects.filter(is_ordered=True).order_by('-created_at')
    return render(request, 'store/custom_admin/order_list.html', {'orders': orders})

@user_passes_test(is_admin)
def admin_order_update(request, order_id):
    # Status Update Logic
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        order.status = status
        order.save()
        messages.success(request, f'Order #{order.id} status updated to {status}')
        return redirect('admin_order_list')
    return redirect('admin_dashboard')

# 1. Product List View
@user_passes_test(is_admin)
def admin_products(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'store/custom_admin/products_list.html', {'products': products})

# 2. Add Product View
@user_passes_test(is_admin)
def admin_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES) # Files zaroori hai image ke liye
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm()
    
    return render(request, 'store/custom_admin/product_form.html', {'form': form, 'title': 'Add New Product'})

# 3. Edit Product View
@user_passes_test(is_admin)
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product) # Instance matlab purana data
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
        
    return render(request, 'store/custom_admin/product_form.html', {'form': form, 'title': 'Edit Product'})

# 4. Delete Product View
@user_passes_test(is_admin)
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('admin_products')

#variants of products color and size
@user_passes_test(is_admin)
def admin_add_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Existing variants dikhane ke liye (Taki pata rahe pehle se kya added hai)
    existing_variants = product.variants.all()

    if request.method == 'POST':
        form = ProductVariantForm(request.POST, request.FILES)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product # Link kar rahe hain ki ye variant kiska hai
            variant.save()
            messages.success(request, 'Variant/Stock added successfully!')
            return redirect('admin_add_variant', product_id=product.id) # Wahi wapas reload karo taki aur add kar sake
    else:
        form = ProductVariantForm()

    context = {
        'product': product,
        'form': form,
        'existing_variants': existing_variants
    }
    return render(request, 'store/custom_admin/add_variant.html', context)

@user_passes_test(is_admin)
def admin_edit_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_id = variant.product.id # Redirect karne ke liye ID save kar li
    
    if request.method == 'POST':
        form = ProductVariantForm(request.POST, request.FILES, instance=variant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variant updated successfully!')
            # Wapas usi product ke variant page par bhejenge
            return redirect('admin_add_variant', product_id=product_id)
    else:
        form = ProductVariantForm(instance=variant)

    context = {
        'form': form,
        'variant': variant,
        'title': f'Edit Variant: {variant.product.name}'
    }
    return render(request, 'store/custom_admin/edit_variant.html', context)

@user_passes_test(is_admin)
def admin_delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_id = variant.product.id
    variant.delete()
    messages.success(request, 'Variant deleted successfully!')
    return redirect('admin_add_variant', product_id=product_id)

# 1. Manage Categories
@user_passes_test(is_admin)
def admin_categories(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.slug = slugify(cat.name) # Name se Slug auto-generate
            cat.save()
            messages.success(request, 'Category added successfully!')
            return redirect('admin_categories')
    else:
        form = CategoryForm()

    return render(request, 'store/custom_admin/manage_category.html', {'form': form, 'categories': categories})

# Category Delete
@user_passes_test(is_admin)
def admin_delete_category(request, id):
    item = get_object_or_404(Category, id=id)
    item.delete()
    messages.success(request, 'Category deleted.')
    return redirect('admin_categories')

# 2. Manage Sizes
@user_passes_test(is_admin)
def admin_sizes(request):
    sizes = Size.objects.all()
    if request.method == 'POST':
        form = SizeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Size added successfully!')
            return redirect('admin_sizes')
    else:
        form = SizeForm()
    return render(request, 'store/custom_admin/manage_size.html', {'form': form, 'sizes': sizes})

# Size Delete
@user_passes_test(is_admin)
def admin_delete_size(request, id):
    item = get_object_or_404(Size, id=id)
    item.delete()
    return redirect('admin_sizes')

# 3. Manage Colors
@user_passes_test(is_admin)
def admin_colors(request):
    colors = Color.objects.all()
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Color added successfully!')
            return redirect('admin_colors')
    else:
        form = ColorForm()
    return render(request, 'store/custom_admin/manage_color.html', {'form': form, 'colors': colors})

# Color Delete
@user_passes_test(is_admin)
def admin_delete_color(request, id):
    item = get_object_or_404(Color, id=id)
    item.delete()
    return redirect('admin_colors')


#bill/invoice ke liye code
@user_passes_test(is_admin)
def admin_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_products = OrderProduct.objects.filter(order=order)
    
    template_path = 'store/custom_admin/invoice.html'
    context = {
        'order': order,
        'order_products': order_products,
    }

    response = HttpResponse(content_type='application/pdf')
    
    # CHANGE HERE: 'attachment' ki jagah 'inline' kar diya
    # Isse PDF browser me khulega. Wahan download button hota hi hai.
    response['Content-Disposition'] = f'inline; filename="Invoice_{order_id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response

#footer section code 
def about(request):
    return render(request, 'store/pages/about.html')

def privacy_policy(request):
    return render(request, 'store/pages/privacy.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']
        
        # Email Body taiyar karna
        full_message = f"From: {name} ({email})\n\nMessage:\n{message}"
        
        # Admin ko mail bhejna (Console me dikhega abhi)
        send_mail(
            subject=f"New Contact Msg: {subject}",
            message=full_message,
            from_email=email,
            recipient_list=['admin@babushonawear.com'], # Asli owner ka email yahan ayega
            fail_silently=False,
        )
        messages.success(request, 'Your message has been sent. We will contact you shortly.')
        return redirect('contact')
        
    return render(request, 'store/pages/contact.html')

#ratig and review code 
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            
            # Yahan 'request.FILES' add karna zaruri hai (Update case me)
            form = ReviewForm(request.POST, request.FILES, instance=reviews)
            
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
            
        except ReviewRating.DoesNotExist:
            # Yahan bhi 'request.FILES' add karo (New case me)
            form = ReviewForm(request.POST, request.FILES)
            
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                
                # Image ko manually assign karo
                data.image = form.cleaned_data['image'] 
                
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)


@login_required(login_url='handle_login')
def edit_profile(request):
    # 1. User Profile dhoondo, agar nahi hai to nayi bana do (Safe tareeka)
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # 2. Forms me data bharo (User wala aur Profile wala)
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        
        # 3. Check karo data sahi hai ya nahi
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile') # Wapas isi page par bhej do
    else:
        # 4. Agar GET request hai (Page khula hai), to purana data dikhao
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'store/dashboard/edit_profile.html', context)

@login_required(login_url='handle_login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Password change hone ke baad user logout na ho, isliye session update karte hain
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Password has been changed successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)

    context = {
        'form': form,
    }
    return render(request, 'store/dashboard/change_password.html', context)

#cart count
def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}

    try:
        cart_items = None
        
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
        else:
            # _cart_id logic yahi likh diya (Import ki jhanjhat khatam)
            cart_id = request.session.session_key
            if not cart_id:
                cart_id = request.session.create()
            
            try:
                cart = Cart.objects.get(cart_id=cart_id)
                cart_items = CartItem.objects.filter(cart=cart)
            except Cart.DoesNotExist:
                cart_count = 0

        if cart_items:
            for cart_item in cart_items:
                cart_count += cart_item.quantity
    except:
        cart_count = 0
        
    return dict(cart_count=cart_count)

# store/views.py

def order_detail(request, order_id):
    order_detail = Order.objects.get(order_number=order_id)
    order_products = OrderProduct.objects.filter(order=order_detail)
    
    context = {
        'order': order_detail,
        'order_products': order_products,
    }
    return render(request, 'store/order_detail.html', context)