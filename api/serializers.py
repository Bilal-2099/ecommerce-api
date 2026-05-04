from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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
    owner = serializers.ReadOnlyField(source="owner.email")

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["owner"]

    def create(self, validated_data):
        user = self.context["request"].user

        if not user.is_business():
            raise serializers.ValidationError("Only business users can create products")

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
        fields = ["id", "cartitems", "total_price", "created_at", "updated_at"]

    def get_total_price(self, obj):
        return sum(item.product.price * item.quantity for item in obj.cartitems.all())

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
        if Wishlist.objects.filter(user=user, product=data["product"]).exists():
            raise serializers.ValidationError("You already wishlisted this product")
        return data

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")

    class Meta:
        model = OrderItem
        fields = ["product", "product_name", "quantity"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["status", "amount", "user", "stripe_checkout_id"]

    def create(self, validated_data):

        items_data = validated_data.pop("items")
        user = self.context["request"].user

        total_amount = 0

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                status="Pending",
                amount=0,
                **validated_data
            )

            for item in items_data:
                product = item["product"]
                quantity = item["quantity"]

                product.refresh_from_db()

                if product.stock < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {product.name}"
                    )

                product.stock -= quantity
                product.save()

                total_amount += product.price * quantity

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity
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