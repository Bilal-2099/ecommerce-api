from django.db import transaction
from rest_framework import permissions, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

# Import drf-spectacular tools
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from ..models import *
from ..permissions import *
from ..serializers import CartSerializer, CartItemSerializer


# Dynamic helper function to wrap response variants uniformly
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'CartData'
    
    return inline_serializer(
        name=f"Wrapped{serializer_name}{'List' if is_list else ''}",
        fields={
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(default=message_example),
            "data": data_field
        }
    )


@extend_schema_view(
    list=extend_schema(
        summary="Retrieve user cart",
        description="Fetches or auto-initializes the active shopping cart for the logged-in user, complete with all nested items and compiled subtotal values.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CartSerializer))}
    )
)
class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self):
        return Cart.objects.get_or_create(
            user=self.request.user
        )[0]

    def list(self, request):
        cart = self.get_cart()
        serializer = CartSerializer(cart)
        
        # Wrapped matching envelope structure manually if needed, or keeping your raw mapping
        return Response({
            "success": True,
            "message": "Cart details retrieved successfully",
            "data": serializer.data
        })


@extend_schema_view(
    list=extend_schema(
        summary="List cart items",
        description="Retrieves a list of individual items currently sitting inside the user's shopping basket.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CartItemSerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="Add item to cart",
        description="Appends a product selection to the cart. Automatically intercepts and builds totals or increments quantities sequentially if items match. Blocks requests exceeding current stock metrics.",
        request=CartItemSerializer,
        responses={
            201: OpenApiResponse(response=get_wrapped_response_schema(CartItemSerializer, message_example="Item added to cart")),
            400: OpenApiResponse(description="Validation error: 'Not enough stock' or 'Exceeds available stock'.")
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve cart item details",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CartItemSerializer))}
    ),
    update=extend_schema(
        summary="Update item quantity (Full Overwrite)",
        request=CartItemSerializer,
        responses={
            200: OpenApiResponse(response=get_wrapped_response_schema(CartItemSerializer)),
            400: OpenApiResponse(description="Stock ceiling allocation failure.")
        }
    ),
    partial_update=extend_schema(
        summary="Modify item metrics (Patch)",
        request=CartItemSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CartItemSerializer))}
    ),
    destroy=extend_schema(
        summary="Remove item from cart",
        responses={204: OpenApiResponse(description="Item eliminated out of the active user session scope.")}
    )
)
class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self):
        return Cart.objects.get_or_create(
            user=self.request.user
        )[0]

    def get_queryset(self):
        return CartItem.objects.filter(
            cart__user=self.request.user
        )

    @extend_schema(
        summary="Clear whole cart",
        description="Deletes every single nested item element stored within the user's active cart layout.",
        responses={
            200: inline_serializer(
                name="CartClearResponse",
                fields={
                    "success": serializers.BooleanField(default=True),
                    "message": serializers.CharField(default="X items removed")
                }
            )
        }
    )
    @action(detail=False, methods=["delete"])
    def clear(self, request):
        cart = self.get_cart()
        deleted_count, _ = cart.cartitems.all().delete()

        return Response({
            "success": True,
            "message": f"{deleted_count} items removed"
        })

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
                if product.stock < (cart_item.quantity + quantity):
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
            product = Product.objects.select_for_update().get(
                id=instance.product.id
            )

            new_quantity = serializer.validated_data.get(
                "quantity",
                instance.quantity
            )

            available_stock = (product.stock + instance.quantity)

            if new_quantity > available_stock:
                raise ValidationError("Not enough stock")

            serializer.save()