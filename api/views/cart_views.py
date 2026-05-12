from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..models import *
from ..permissions import *
from ..serializers import *


class CartViewSet(viewsets.ViewSet):

    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self):
        return Cart.objects.get_or_create(
            user=self.request.user
        )[0]

    def list(self, request):

        cart = self.get_cart()

        serializer = CartSerializer(cart)

        return Response(serializer.data)


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

    @action(detail=False, methods=["delete"])
    def clear(self, request):

        cart = self.get_cart()

        deleted_count, _ = cart.cartitems.all().delete()

        return Response({
            "message": f"{deleted_count} items removed"
        })

    def perform_create(self, serializer):

        cart = self.get_cart()

        with transaction.atomic():

            product = Product.objects.select_for_update().get(
                id=serializer.validated_data["product"].id
            )

            quantity = serializer.validated_data.get(
                "quantity",
                1
            )

            if product.stock < quantity:
                raise ValidationError("Not enough stock")

            cart_item = (
                CartItem.objects.select_for_update()
                .filter(cart=cart, product=product)
                .first()
            )

            if cart_item:

                if product.stock < (
                    cart_item.quantity + quantity
                ):
                    raise ValidationError(
                        "Exceeds available stock"
                    )

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

            available_stock = (
                product.stock + instance.quantity
            )

            if new_quantity > available_stock:
                raise ValidationError("Not enough stock")

            serializer.save()