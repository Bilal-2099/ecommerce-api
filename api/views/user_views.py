from django.contrib.auth import get_user_model, update_session_auth_hash
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

# Import drf-spectacular tools
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, inline_serializer

from ..models import CustomUser
from ..serializers import (
    UserSerializer, 
    ChangePasswordSerializer, 
    CustomTokenSerializer
)

User = get_user_model()


# Dynamic helper function to wrap User responses in your standardized success/message envelope
def get_wrapped_response_schema(data_serializer, is_list=False, message_example="Success"):
    if is_list:
        data_field = serializers.ListField(child=data_serializer())
    else:
        data_field = data_serializer() if isinstance(data_serializer, type) else data_serializer

    serializer_name = data_serializer.__name__ if hasattr(data_serializer, '__name__') else 'UserData'
    
    return inline_serializer(
        name=f"Wrapped{serializer_name}{'List' if is_list else ''}",
        fields={
            "success": serializers.BooleanField(default=True),
            "message": serializers.CharField(default=message_example),
            "data": data_field
        }
    )


# =====================================================================
# JWT AUTHENTICATION ENDPOINT
# =====================================================================

@extend_schema(
    summary="Obtain JSON Web Token (Login)",
    description="Takes user email credentials and returns a pair of Access and Refresh JWT tokens upon verification.",
    request=CustomTokenSerializer,
    responses={
        200: inline_serializer(
            name="JWTTokenResponse",
            fields={
                "access": serializers.CharField(),
                "refresh": serializers.CharField()
            }
        ),
        401: OpenApiResponse(description="No active account found with the given credentials.")
    }
)
class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


# =====================================================================
# PASSWORD MANAGEMENT FUNCTIONAL VIEW
# =====================================================================

@extend_schema(
    methods=["POST"],
    summary="Change account password",
    description="Allows the currently authenticated user to update their account password after validating their old credentials.",
    request=ChangePasswordSerializer,
    responses={
        200: inline_serializer(
            name="PasswordChangeSuccess",
            fields={
                "success": serializers.BooleanField(default=True),
                "message": serializers.CharField(default="Password changed successfully")
            }
        ),
        400: OpenApiResponse(description="Validation Error: 'Incorrect old password' or mismatched validation syntax rules.")
    }
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)

    if serializer.is_valid():
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"success": False, "error": "Incorrect old password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        
        # Flush and sync session authentication signatures to prevent automated logouts
        update_session_auth_hash(request, user)

        return Response(
            {"success": True, "message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )

    return Response(
        {"success": False, "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )


# =====================================================================
# USER PROFILE MANAGEMENT VIEWSET
# =====================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List user records",
        description="Retrieves registration profiles. Staff users see all entries; standard users only see their own account line entry.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(UserSerializer, is_list=True))}
    ),
    create=extend_schema(
        summary="Register a new user account",
        description="Public registration portal to provision new user credential profiles.",
        request=UserSerializer,
        responses={201: OpenApiResponse(response=get_wrapped_response_schema(UserSerializer, message_example="Account provisioned successfully"))}
    ),
    retrieve=extend_schema(
        summary="Retrieve profile specifics",
        description="Fetches properties associated with a single registration index identifier.",
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(UserSerializer))}
    ),
    update=extend_schema(
        summary="Update user details (Full Overwrite)",
        request=UserSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(UserSerializer))}
    ),
    partial_update=extend_schema(
        summary="Modify user profile properties (Patch)",
        request=UserSerializer,
        responses={200: OpenApiResponse(response=get_wrapped_response_schema(UserSerializer))}
    ),
    destroy=extend_schema(
        summary="Terminate/Delete a user profile index entry",
        responses={204: OpenApiResponse(description="Account completely removed.")}
    )
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        # Multitenant isolation rule logic
        if self.request.user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=self.request.user.id)

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]