from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import *


urlpatterns = [
    path('change_password/', change_password, name='change_password')
]

router = DefaultRouter()

router.register("users", UserViewSet, basename="user")
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("carts", CartViewSet, basename="cart") 
router.register("cart-items", CartItemViewSet, basename='cart-item') 
router.register("reviews", ReviewViewSet, basename='review')
router.register("wishlist", WishlistViewSet, basename='wishlist')
router.register("orders", OrderViewSet, basename='order')
router.register("addresses", CustomerAddressViewSet, basename='address')

urlpatterns += router.urls
