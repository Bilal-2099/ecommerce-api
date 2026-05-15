from rest_framework import viewsets, permissions, serializers

# Import drf-spectacular tools
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from ..models import CustomerAddress
from ..serializers import CustomerAddressSerializer


# Dynamic helper function to wrap Address responses in your standardized success/message envelope
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'AddressData'
    
    return inline_serializer(
        name=f"Wrapped{serializer_name}{'List' if is_list else ''}",
        fields={
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(default=message_example),
            "data": data_field
        }
    )


# Attach custom Swagger documentation to the auto-generated ViewSet actions
@extend_schema_view(
    list=extend_schema(
        summary="List user addresses",
        description="Retrieves all saved addresses belonging strictly to the currently authenticated user.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CustomerAddressSerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="Create a new address",
        description="Saves a new address profile. Note: The 'customer' relationship is implicitly bound to your active authentication token.",
        request=CustomerAddressSerializer,
        responses={
            201: OpenApiResponse(response=get_wrapped_response_schema(CustomerAddressSerializer, message_example="Address saved successfully")),
            400: OpenApiResponse(description="Invalid request payload data."),
            401: OpenApiResponse(description="Authentication required.")
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve specific address details",
        description="Fetch details of an address using its ID lookup (Only accessible if the address belongs to you).",
        responses={
            200: OpenApiResponse(response=get_wrapped_response_schema(CustomerAddressSerializer)),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Address not found or permission denied.")
        }
    ),
    update=extend_schema(
        summary="Update address details (Full Overwrite)",
        description="Completely overwrites an existing address card configuration.",
        request=CustomerAddressSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CustomerAddressSerializer))}
    ),
    partial_update=extend_schema(
        summary="Modify address attributes (Patch)",
        description="Partially updates address properties (like fixing a typo in the street name).",
        request=CustomerAddressSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CustomerAddressSerializer))}
    ),
    destroy=extend_schema(
        summary="Delete a saved address",
        description="Permanently drops an address out of the user's saved account settings profile map.",
        responses={
            204: OpenApiResponse(description="Address deleted successfully."),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Address not found.")
        }
    )
)
class CustomerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Keeps data isolated so users can only view, modify, or delete their own items
        return CustomerAddress.objects.filter(customer=self.request.user)