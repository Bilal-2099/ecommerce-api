from ..serializers import *
from rest_framework import serializers

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = "__all__"

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)