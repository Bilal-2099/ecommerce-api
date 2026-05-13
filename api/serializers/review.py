from ..serializers import *
from rest_framework import serializers

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
