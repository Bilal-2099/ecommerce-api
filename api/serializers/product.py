from rest_framework import serializers
from ..models import Product
from ..serializers import *

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