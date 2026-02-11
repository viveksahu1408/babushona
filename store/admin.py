from django.contrib import admin
from .models import Category, Size, Color, Product, ProductVariant, Cart, CartItem, Order, OrderProduct,UserProfile
from .models import Product, Category, ReviewRating # <-- ReviewRating add kiya
from django.utils.html import format_html

# Product ke andar hi Variants dikhane ke liye (Inline)
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    inlines = [ProductVariantInline] # Isse product add karte time hi size/stock daal paoge
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Size)
admin.site.register(Color)
admin.site.register(Product, ProductAdmin)

# Order ke items ko Order ke andar hi dikhane ke liye (Inline)
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('product_variant', 'product_price', 'quantity', 'sub_total')
    extra = 0
    
    def sub_total(self, obj):
        # Yahan hum check kar rahe hain ki value exist karti hai ya nahi
        if obj.quantity and obj.product_price:
            return obj.quantity * obj.product_price
        return 0  # Agar value nahi hai to 0 return karo (Crash nahi hoga)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'phone', 'email', 'order_total', 'status', 'is_ordered', 'tracking_number', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['id', 'first_name', 'phone', 'email']
    list_editable = ['status', 'tracking_number']
    list_per_page = 20
    inlines = [OrderProductInline] # Isse order kholte hi andar dikhega ki kya saman mangwaya hai

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct)
admin.site.register(Cart) # Debugging ke liye Cart bhi dekh sakte ho


# --- Category ke liye ye add kar ---
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)} # Jaise hi Name likhoge, Slug apne aap ban jayega
    list_display = ('name', 'slug')

# Purana register hata kar ye naya wala lagana:
admin.site.register(Category, CategoryAdmin) 

# --- Review Admin Configuration ---
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ['subject', 'rating', 'product', 'user', 'status', 'created_at','image']
    list_editable = ['status'] # Bahar se hi True/False kar sakoge
    readonly_fields = ['ip', 'user', 'product', 'rating', 'subject', 'review','image'] # Admin bas dekh sake, edit na kare (security)

admin.site.register(ReviewRating, ReviewRatingAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    # Admin list me photo dikhane ke liye function
    def thumbnail(self, object):
        if object.profile_picture:
            return format_html('<img src="{}" width="30" style="border-radius:50%;">'.format(object.profile_picture.url))
        return "No Image"
    thumbnail.short_description = 'Profile Picture'
    
    list_display = ('thumbnail', 'user', 'city', 'state', 'country')

admin.site.register(UserProfile, UserProfileAdmin)