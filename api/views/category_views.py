from rest_framework import viewsets, permissions, serializers
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from ..models import Category
from ..serializers import CategorySerializer


# Dynamic helper function to wrap Category responses in your standardized success/message envelope
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'CategoryData'
    
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
        summary="List all product categories",
        description="Retrieves a list of all active categories. Open to the public.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CategorySerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="Create a new category",
        description="Adds a new product category to the system. Requires authentication.",
        request=CategorySerializer,
        responses={
            201: OpenApiResponse(response=get_wrapped_response_schema(CategorySerializer, message_example="Category created successfully")),
            400: OpenApiResponse(description="Invalid request payload data."),
            401: OpenApiResponse(description="Authentication credentials were not provided.")
        }
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific category",
        description="Fetch specific category details using its unique database ID.",
        responses={
            200: OpenApiResponse(response=get_wrapped_response_schema(CategorySerializer)),
            404: OpenApiResponse(description="Category not found.")
        }
    ),
    update=extend_schema(
        summary="Update a category (Full Overwrite)",
        description="Completely overwrites an existing category entry. Requires authentication.",
        request=CategorySerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CategorySerializer))}
    ),
    partial_update=extend_schema(
        summary="Modify category details (Patch)",
        description="Partially updates specific attributes of a category without sending the full payload.",
        request=CategorySerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(CategorySerializer))}
    ),
    destroy=extend_schema(
        summary="Delete a category",
        description="Permanently deletes a category from the database. Requires authentication.",
        responses={
            204: OpenApiResponse(description="Category successfully deleted (No Content)."),
            401: OpenApiResponse(description="Authentication credentials were not provided."),
            404: OpenApiResponse(description="Category not found.")
        }
    )
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]