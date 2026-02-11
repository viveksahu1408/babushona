from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [ 
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/',views.cart,name='cart'),

   # Add to cart (Product Page se)
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    
    # Cart Modification URLs (Cart Page buttons ke liye)
    path('add_qty/<int:cart_item_id>/', views.add_qty_cart, name='add_qty_cart'),
    path('remove_cart/<int:cart_item_id>/', views.remove_cart, name='remove_cart'),
    path('remove_cart_item/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'),

    #checkout code logic
    path('checkout/', views.checkout, name='checkout'),
    path('place_order/', views.place_order, name='place_order'),
    
    #order track karne ke liye hai
    path('track/', views.track_order, name='track_order'),  
    #this is for signup login
    path('register/', views.handle_register, name='handle_register'),
    path('login/', views.handle_login, name='handle_login'),
    path('logout/', views.handle_logout, name='handle_logout'),

    path('dashboard/', views.dashboard, name='dashboard'),

    #forget password
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="store/password_reset.html"), 
         name="reset_password"),

    # 2. Email Sent Success Page
    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="store/password_reset_sent.html"), 
         name="password_reset_done"),

    # 3. Link Click karne par New Password wala page
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="store/password_reset_form.html"), 
         name="password_reset_confirm"),

    # 4. Password Change Success Page
    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="store/password_reset_done.html"), 
         name="password_reset_complete"),

    # Store URLs
    path('store/', views.store, name='store'),
    path('store/category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('store/search/', views.search, name='search'),
  
     # Custom Admin URLs
     path('my-admin/', views.admin_dashboard, name='admin_dashboard'),
     path('my-admin/orders/', views.admin_order_list, name='admin_order_list'),
     path('my-admin/update_order/<int:order_id>/', views.admin_order_update, name='admin_order_update'),

     # url admin dashboard vale
     path('my-admin/products/', views.admin_products, name='admin_products'),
     path('my-admin/products/add/', views.admin_add_product, name='admin_add_product'),
     path('my-admin/products/edit/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
     path('my-admin/products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),

     path('my-admin/products/variant/<int:product_id>/', views.admin_add_variant, name='admin_add_variant'),

     path('my-admin/variant/edit/<int:variant_id>/', views.admin_edit_variant, name='admin_edit_variant'),
     path('my-admin/variant/delete/<int:variant_id>/', views.admin_delete_variant, name='admin_delete_variant'),

     # Master Data URLs
     path('my-admin/categories/', views.admin_categories, name='admin_categories'),
     path('my-admin/categories/delete/<int:id>/', views.admin_delete_category, name='admin_delete_category'),

     path('my-admin/sizes/', views.admin_sizes, name='admin_sizes'),
     path('my-admin/sizes/delete/<int:id>/', views.admin_delete_size, name='admin_delete_size'),

     path('my-admin/colors/', views.admin_colors, name='admin_colors'),
     path('my-admin/colors/delete/<int:id>/', views.admin_delete_color, name='admin_delete_color'),

     # store/urls.py me ye path add karo:
     path('my-admin/invoice/<int:order_id>/', views.admin_invoice, name='admin_invoice'),
    
     # footer pages ke liye 
     path('about/', views.about, name='about'),
     path('contact/', views.contact, name='contact'),
     path('privacy-policy/', views.privacy_policy, name='privacy'),
     path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
     # store/urls.py
     path('dashboard/edit_profile/', views.edit_profile, name='edit_profile'),
# store/urls.py me ye line add karo:
     path('dashboard/change_password/', views.change_password, name='change_password'),
     path('order_detail/<str:order_id>/', views.order_detail, name='order_detail'),


]