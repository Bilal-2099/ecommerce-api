from django.contrib.auth import update_session_auth_hash
from ..models import *
from ..permissions import *
from ..serializers import *
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):

    serializer = ChangePasswordSerializer(data=request.data)

    if serializer.is_valid():

        user = request.user

        if not user.check_password(
            serializer.validated_data["old_password"]
        ):
            return Response(
                {"error": "Incorrect old password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(
            serializer.validated_data["new_password"]
        )

        user.save()

        update_session_auth_hash(request, user)

        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )