from rest_framework import serializers
from django.db.models import F, Sum, DecimalField
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import *
from decimal import Decimal
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)



class CustomTokenSerializer(TokenObtainPairSerializer):
    username_field = "email"


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "username", "email", "password", "user_type", "profile_picture_url"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class ProductSerializer(serializers.ModelSerializer):
    owner_email = serializers.ReadOnlyField(source="owner.email")

    class Meta:
        model = Product
        exclude = ["owner"]

    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        user = request.user

        if not user.is_business():
            raise serializers.ValidationError("Only business users allowed")

        validated_data["owner"] = user
        return super().create(validated_data)

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

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Review
        fields = "__all__"

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        user = self.context["request"].user
        if Review.objects.filter(user=user, product=data["product"]).exists():
            raise serializers.ValidationError("You already reviewed this product")
        return data

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = "__all__"

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        user = self.context["request"].user
        # if Wishlist.objects.filter(user=user, product=data["product"]).exists():
        #     raise serializers.ValidationError("You already wishlisted this product")
        return data

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

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = "__all__"

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)