from ..models import *
from ..permissions import *
from ..serializers import *
from rest_framework import viewsets

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]