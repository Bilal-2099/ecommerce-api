from rest_framework import viewsets, permissions, serializers

# Import drf-spectacular tools
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from ..models import Order
from ..serializers import OrderSerializer


# Dynamic helper function to wrap Order responses in your standardized success/message envelope
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'OrderData'
    
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
        summary="List all order histories",
        description="Retrieves a history of past orders completed by the currently logged-in user.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(OrderSerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="Place a new order (Checkout)",
        description=(
            "Submits a multi-item purchase checkout. This operation runs inside a database transaction lock "
            "to check product inventory, safely deduct stock quantities, and automatically calculate final subtotal pricing."
        ),
        request=OrderSerializer,
        responses={
            201: OpenApiResponse(
                response=get_wrapped_response_schema(OrderSerializer, message_example="Order processed successfully"),
                description="Order created successfully. Returns calculated total amount and currency."
            ),
            400: OpenApiResponse(description="Validation Error: One or more requested items do not have enough stock available."),
            401: OpenApiResponse(description="Authentication required.")
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve specific order details",
        description="Fetches an existing invoice order summary configuration matching the provided record ID.",
        responses={
            200: OpenApiResponse(response=get_wrapped_response_schema(OrderSerializer)),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Order ID not found or access permission denied.")
        }
    ),
    update=extend_schema(
        summary="Replace order data (Full Overwrite)",
        description="Completely overwrites an existing order schema record.",
        request=OrderSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(OrderSerializer))}
    ),
    partial_update=extend_schema(
        summary="Modify order details (Patch)",
        description="Applies partial updates to a user order structure record line.",
        request=OrderSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(OrderSerializer))}
    ),
    destroy=extend_schema(
        summary="Cancel/Delete an order record",
        description="Removes an order listing out of the user profile database history tables.",
        responses={
            204: OpenApiResponse(description="Order dropped cleanly (No Content)."),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Order not found.")
        }
    )
)
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can view and manage their own past orders only
        return Order.objects.filter(user=self.request.user)