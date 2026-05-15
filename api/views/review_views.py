from rest_framework import viewsets, permissions, serializers
from django.db.models import Avg, Count

# Import drf-spectacular tools
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from ..models import Review, ProductRating
from ..serializers import ReviewSerializer
from ..permissions import IsOwner


# Dynamic helper function to wrap Review responses in your standardized success/message envelope
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'ReviewData'
    
    return inline_serializer(
        name=f"Wrapped{serializer_name}{'List' if is_list else ''}",
        fields={
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(default=message_example),
            "data": data_field
        }
    )


# Attach custom Swagger documentation to your review pipeline views
@extend_schema_view(
    list=extend_schema(
        summary="List all reviews",
        description="Retrieves a list of all product reviews submitted across the platform.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(ReviewSerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="Submit a product review",
        description=(
            "Adds a review and rating score to a product. Note: A user can only submit one review per product. "
            "Submitting a second review will fail. Successful submissions automatically recalculate the product's overall rating score metrics."
        ),
        request=ReviewSerializer,
        responses={
            201: OpenApiResponse(response=get_wrapped_response_schema(ReviewSerializer, message_example="Review submitted successfully")),
            400: OpenApiResponse(description="Validation Error: 'You already reviewed this product' or missing required fields."),
            401: OpenApiResponse(description="Authentication required.")
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve specific review details",
        description="Fetches individual comment text and scoring allocations using the unique Review ID reference number.",
        responses={
            200: OpenApiResponse(response=get_wrapped_response_schema(ReviewSerializer)),
            404: OpenApiResponse(description="Review ID not found.")
        }
    ),
    update=extend_schema(
        summary="Update a review (Full Overwrite)",
        description="Overwrites an existing review message block. Automatically recalculates corresponding product rating metrics aggregates.",
        request=ReviewSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(ReviewSerializer))}
    ),
    partial_update=extend_schema(
        summary="Modify a review (Patch)",
        description="Allows partial updates (like modifying just the star rating score or text comment) on an existing review entry.",
        request=ReviewSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(ReviewSerializer))}
    ),
    destroy=extend_schema(
        summary="Delete a product review",
        description="Permanently drops a review line record out of the application databases. Updates global averages automatically.",
        responses={
            204: OpenApiResponse(description="Review deleted successfully (No Content)."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Permission Denied: You do not have permission to delete this review profile record.")
        }
    )
)
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