from django.db.models import Q
from rest_framework import permissions, viewsets, serializers

# Import drf-spectacular tools
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiParameter, inline_serializer

from ..models import Product
from ..serializers import ProductSerializer
from ..permissions import IsBusinessUser, IsOwnerOrReadOnly


# Dynamic helper function to wrap Product responses in your standardized success/message envelope
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'ProductData'
    
    return inline_serializer(
        name=f"Wrapped{serializer_name}{'List' if is_list else ''}",
        fields={
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(default=message_example),
            "data": data_field
        }
    )


# Attach custom Swagger documentation to the dynamically protected ViewSet actions
@extend_schema_view(
    list=extend_schema(
        summary="List marketplace products",
        description="Retrieves a list of all items currently available in the catalog. Open to the public.",
        parameters=[
            OpenApiParameter(
                name="category",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter items by supplying either a numeric Category ID or its corresponding unique text string URL slug."
            )
        ],
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(ProductSerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="List a new product listing",
        description="Allows commercial profiles to publish new inventory rows. Restricted exclusively to verified Business Users.",
        request=ProductSerializer,
        responses={
            201: OpenApiResponse(response=get_wrapped_response_schema(ProductSerializer, message_example="Item published successfully")),
            400: OpenApiResponse(description="Validation Error: User must be authenticated and have an active commercial/business account role."),
            403: OpenApiResponse(description="Permission Denied: Authenticated account is not registered as a business vendor.")
        }
    ),
    retrieve=extend_schema(
        summary="Get individual product profiles",
        description="Fetches comprehensive specification attributes of an inventory listing utilizing its unique ID reference indicator.",
        responses={
            200: OpenApiResponse(response=get_wrapped_response_schema(ProductSerializer)),
            404: OpenApiResponse(description="Product record does not exist within the catalog tables.")
        }
    ),
    update=extend_schema(
        summary="Update product details (Full Overwrite)",
        description="Completely overwrites an existing product layout definition. Restricted to the user who originally created the record.",
        request=ProductSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(ProductSerializer))}
    ),
    partial_update=extend_schema(
        summary="Modify product attributes (Patch)",
        description="Modifies specific product data blocks (such as updates to prices or adjusting stock balances) without modifying the full entry.",
        request=ProductSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(ProductSerializer))}
    ),
    destroy=extend_schema(
        summary="Permanently delete a product listing",
        description="Completely removes an inventory profile row out of the public catalog. restricted strictly to the original listing owner.",
        responses={
            204: OpenApiResponse(description="Product successfully removed (No Content)."),
            403: OpenApiResponse(description="Permission Denied: You do not own this product listing configuration.")
        }
    )
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        # Action-specific security contexts are parsed correctly inside the schema view above
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