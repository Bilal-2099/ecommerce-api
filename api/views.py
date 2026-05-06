from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import update_session_auth_hash
from .serializers import ChangePasswordSerializer
from django.db import transaction
from rest_framework.exceptions import ValidationError

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import update_session_auth_hash
from .serializers import ChangePasswordSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    if request.method == 'POST':
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                update_session_auth_hash(request, user)  # To update session after password change
                return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Incorrect old password.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False


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

    def get_cart(self):
        return Cart.objects.get_or_create(user=self.request.user)[0]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self):
        return Cart.objects.get_or_create(user=self.request.user)[0]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        cart = self.get_cart()
        deleted_count, _ = cart.cartitems.all().delete()
        return Response({"message": f"{deleted_count} items removed"})

    def perform_create(self, serializer):
        cart = self.get_cart()

        with transaction.atomic():
            product = Product.objects.select_for_update().get(
                id=serializer.validated_data["product"].id
            )

            quantity = serializer.validated_data.get("quantity", 1)

            if product.stock < quantity:
                raise ValidationError("Not enough stock")

            cart_item = (
                CartItem.objects.select_for_update()
                .filter(cart=cart, product=product)
                .first()
            )

            if cart_item:
                if product.stock < cart_item.quantity + quantity:
                    raise ValidationError("Exceeds available stock")

                cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=quantity
                )

        serializer.instance = cart_item

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = self.get_object()

            product = Product.objects.select_for_update().get(id=instance.product.id)

            new_quantity = serializer.validated_data.get("quantity", instance.quantity)

            available_stock = product.stock + instance.quantity

            if new_quantity > available_stock:
                raise ValidationError("Not enough stock")

            serializer.save()

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def perform_create(self, serializer):
        review = serializer.save(user=self.request.user)
        self.update_product_rating(review.product)

    def perform_update(self, serializer):
        review = serializer.save()
        self.update_product_rating(review.product)

    def perform_destroy(self, instance):
        product = instance.product
        instance.delete()
        self.update_product_rating(product)

    def update_product_rating(self, product):
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

