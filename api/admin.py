from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


admin.site.register(CustomUser)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(ProductRating)
admin.site.register(Wishlist)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(CustomerAddress)