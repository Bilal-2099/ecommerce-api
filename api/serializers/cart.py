from ..models import *
from rest_framework import serializers
from django.db.models import F, Sum, DecimalField
from ..models import *

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "quantity"]

class CartSerializer(serializers.ModelSerializer):
    cartitems = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "cartitems", "total_price"]

    def get_total_price(self, obj):
        result = obj.cartitems.aggregate(
            total=Sum(
                F("quantity") * F("product__price"),
                output_field=DecimalField()
            )
        )
        return result["total"] or 0
