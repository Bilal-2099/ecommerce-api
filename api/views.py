import stripe 
from rest_framework.decorators import action
from django.db.models import Avg, Count
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import *
from .serializers import *
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
# stripe.api_key = settings.STRIPE_SECRET_KEY
# endpoint_secret = settings.WEBHOOK_SECRET

# User = get_user_model()

from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

class IsBusinessUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_business()


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=self.request.user.id)

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.IsAuthenticated(), IsBusinessUser()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = Product.objects.all()

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                Q(category__id=category) | Q(category__slug=category)
            )

        return queryset

class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)

    def get_object(self):
        obj = super().get_object()
        if obj.cart.user != self.request.user:
            raise PermissionDenied("Not your cart item")
        return obj

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.cartitems.all().delete()
        return Response({"message": "Cart cleared"})

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)

        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)


        if product.stock < quantity:
            raise serializers.ValidationError("Not enough stock")

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            if product.stock < cart_item.quantity + quantity:
                raise serializers.ValidationError("Exceeds available stock")

            cart_item.quantity += quantity
            cart_item.save()

        serializer.instance = cart_item
    
    def perform_update(self, serializer):
        instance = self.get_object()
        new_quantity = serializer.validated_data.get("quantity", instance.quantity)

        available_stock = instance.product.stock + instance.quantity

        if new_quantity > available_stock:
            raise serializers.ValidationError("Not enough stock")

        serializer.save()

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def perform_create(self, serializer):
        product = serializer.validated_data["product"]

        if product.owner == self.request.user:
            raise PermissionDenied("You cannot review your own product")

        review = serializer.save(user=self.request.user)

        stats = product.reviews.aggregate(
            avg=Avg("rating"),
            count=Count("id")
        )

        ProductRating.objects.update_or_create(
            product=product,
            defaults={
                "average_rating": stats["avg"] or 0,
                "total_reviews": stats["count"]
            }
        )


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class CustomerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerAddress.objects.filter(customer=self.request.user)

