from django.contrib import admin
from .models import Region, Category, Brand, Product, Cart, CartItem, Order, News


admin.site.register(Region)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(News)