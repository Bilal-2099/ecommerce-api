from rest_framework import viewsets, permissions, serializers

# Import drf-spectacular tools
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from api.models import Wishlist
from ..serializers import WishlistSerializer
from ..permissions import IsOwner


# Dynamic helper function to wrap Wishlist responses in your standardized success/message envelope
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'WishlistData'
    
    return inline_serializer(
        name=f"Wrapped{serializer_name}{'List' if is_list else ''}",
        fields={
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(default=message_example),
            "data": data_field
        }
    )


# Attach custom Swagger documentation to your Wishlist pipeline views
@extend_schema_view(
    list=extend_schema(
        summary="List all wishlisted items",
        description="Retrieves a list of all products saved or bookmarked by the currently authenticated user.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(WishlistSerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="Add an item to wishlist",
        description=(
            "Saves a product to the user's wishlist profile. Note: The 'user' relationship is automatically "
            "injected from your active bearer token session metadata, so it can be omitted from the JSON request body."
        ),
        request=WishlistSerializer,
        responses={
            201: OpenApiResponse(response=get_wrapped_response_schema(WishlistSerializer, message_example="Item successfully added to your wishlist.")),
            400: OpenApiResponse(description="Validation Error: Missing required product identifier or invalid data formats."),
            401: OpenApiResponse(description="Authentication required.")
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve specific wishlist entry",
        description="Fetches details of a specific saved wishlist mapping index using its unique ID identifier.",
        responses={
            200: OpenApiResponse(response=get_wrapped_response_schema(WishlistSerializer)),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Wishlist entry not found or permission denied.")
        }
    ),
    update=extend_schema(
        summary="Update a wishlist item (Full Overwrite)",
        description="Completely overwrites a specific wishlist entry row metadata configuration.",
        request=WishlistSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(WishlistSerializer))}
    ),
    partial_update=extend_schema(
        summary="Modify wishlist item attributes (Patch)",
        description="Applies partial field modifications to a saved wishlist entry configuration row.",
        request=WishlistSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(WishlistSerializer))}
    ),
    destroy=extend_schema(
        summary="Remove item from wishlist",
        description="Permanently drops a saved item out of the user's active personal wishlist index.",
        responses={
            204: OpenApiResponse(description="Item removed from wishlist successfully (No Content)."),
            401: OpenApiResponse(description="Authentication required."),
            403: OpenApiResponse(description="Permission Denied: You do not have permission to modify this wishlist instance.")
        }
    )
)
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Strict row isolation: Users can only see, read, or modify entries they created
        return Wishlist.objects.filter(user=self.request.user)