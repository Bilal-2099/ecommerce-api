from rest_framework.decorators import  permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count
from rest_framework import viewsets, permissions
from ..models import *
from ..permissions import *
from ..serializers import *

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def perform_create(self, serializer):
        review = serializer.save(user=self.request.user)
        self.update_product_rating(review.product)

    def perform_update(self, serializer):
        review = serializer.save()
        self.update_product_rating(review.product)

    def perform_destroy(self, instance):
        product = instance.product
        instance.delete()
        self.update_product_rating(product)

    def update_product_rating(self, product):
        stats = product.reviews.aggregate(
            avg=Avg("rating"),
            count=Count("id")
        )

        ProductRating.objects.update_or_create(
            product=product,
            defaults={
                "average_rating": stats["avg"] or 0,
                "total_reviews": stats["count"]
            }
        )