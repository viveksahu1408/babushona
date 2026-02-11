from django.db import models
from django.utils.html import mark_safe
from django.urls import reverse # Import add karo upar
from django.db.models import Avg, Count
from django.contrib.auth.models import User  # <--- Ye line add karo

# 1. Category Table (e.g., Men, Women, Kids)
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

# 2. Size Table (e.g., S, M, L, XL)
class Size(models.Model):
    name = models.CharField(max_length=20) # Example: Medium
    code = models.CharField(max_length=10) # Example: M

    def __str__(self):
        return self.name

# 3. Color Table (e.g., Red, Blue)
class Color(models.Model):
    name = models.CharField(max_length=50) # Example: Red
    code = models.CharField(max_length=20) # Example: #FF0000 (Color picker ke liye)

    def __str__(self):
        return self.name

# 4. Main Product Table
class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Base Price
    old_price = models.IntegerField(default=0, blank=True, null=True)
    image = models.ImageField(upload_to='products/') # Main display image
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count
    def __str__(self):
        return self.name

# 5. Product Variants (Ye handle karega stock, size aur color)
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0) # Kitne bache hain is specific type ke
    image_variant = models.ImageField(upload_to='products/variants/', blank=True, null=True) # Agar color alag h to photo alag hogi

    class Meta:
        unique_together = ('product', 'size', 'color') # Ek hi product ka same size+color duplicate na ho

    def __str__(self):
        return f"{self.product.name} - {self.size.code} - {self.color.name}"
    
# ... purane code ke niche ...

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True) # <--- YE LINE ADD KARNI HAI
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product_variant.product.price * self.quantity

    def __str__(self):
        return str(self.product_variant)
    
#order code

class Order(models.Model):
    # Customer Details
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    
    # Address Details
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=10)
    order_number = models.CharField(max_length=20, blank=True, null=True)
    payment_phone = models.CharField(max_length=15, blank=True, null=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)
    # Order Info
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='New', choices=(
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ))
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.first_name}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of purchase
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def sub_total(self):
        return self.product_price * self.quantity
    
    
    def __str__(self):
        return self.product_variant.product.name    
    
#review and rating
class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='reviews/images/', blank=True, null=True)

    def __str__(self):
        return self.subject    
    
# store/models.py ke last me ye jodo:

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Ek User ki Ek hi Profile hogi
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    profile_picture = models.ImageField(blank=True, upload_to='userprofile/')
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)

    def __str__(self):
        return self.user.first_name    