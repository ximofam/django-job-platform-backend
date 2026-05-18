from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.jobs.models import Category
from apps.jobs.serializers.category_serializer import CategorySerializer


class CategoryTreeAPIView(generics.ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
