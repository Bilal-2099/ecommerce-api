from rest_framework import serializers
from django.db import transaction
from ..models import *
from ..serializers import *
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    product_name = serializers.ReadOnlyField(source="product.name")
    price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ["product", "product_name", "quantity", "price"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ["id", "items", "amount", "currency", "user"]
        read_only_fields = ["user", "amount", "currency"]

    def create(self, validated_data):

        items_data = validated_data.pop("items")
        user = self.context["request"].user

        total_amount = Decimal("0.00")

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                amount=0,
                currency="PKR",
                **validated_data
            )

            for item in items_data:
                product = Product.objects.select_for_update().get(id=item["product"].id)

                if product.stock < item["quantity"]:
                    raise serializers.ValidationError("Not enough stock")

                product.stock -= item["quantity"]
                product.save()

                total_amount += product.price * item["quantity"]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    price=product.price
                )
            order.amount = total_amount
            order.save()

        return order