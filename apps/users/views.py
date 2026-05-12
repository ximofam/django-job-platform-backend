from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated

from apps.users.models import Country
from apps.users.serializers import CountrySerializer


class CountryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
