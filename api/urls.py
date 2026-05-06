from django.urls import path
from .views import change_password

urlpatterns = [
    path('change_password/', change_password, name='change_password')
]

from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()

router.register("users", UserViewSet, basename="user") #To register User
router.register("categories", CategoryViewSet, basename="category") #No auth needed
router.register("products", ProductViewSet, basename="product") #No auth needed
router.register("carts", CartViewSet, basename="cart") #Auth needed
router.register("cart-items", CartItemViewSet, basename='cart-item') #Auth needed
router.register("reviews", ReviewViewSet, basename='review') #Auth needed
router.register("wishlist", WishlistViewSet, basename='wishlist') #Auth needed
router.register("orders", OrderViewSet, basename='order')
router.register("addresses", CustomerAddressViewSet, basename='address')

urlpatterns += router.urls
