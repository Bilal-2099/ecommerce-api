from django.db.models import Q
from rest_framework import permissions, viewsets

from ..models import Product
from ..serializers import ProductSerializer
from ..permissions import (
    IsBusinessUser,
    IsOwnerOrReadOnly
)


class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):

        if self.action == "create":
            return [
                permissions.IsAuthenticated(),
                IsBusinessUser()
            ]

        elif self.action in [
            "update",
            "partial_update",
            "destroy"
        ]:
            return [
                permissions.IsAuthenticated(),
                IsOwnerOrReadOnly()
            ]

        return [permissions.AllowAny()]

    def get_queryset(self):

        queryset = Product.objects.all()

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                Q(category__id=category)
                | Q(category__slug=category)
            )

        return queryset