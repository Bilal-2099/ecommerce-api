from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, permissions
from ..models import *
from ..permissions import *
from ..serializers import *

class CustomerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomerAddress.objects.filter(customer=self.request.user)