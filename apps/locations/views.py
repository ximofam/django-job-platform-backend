from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.locations.models import Country, City, District
from apps.locations.serializers import CountrySerializer, CitySerializer, DistrictSerializer


class CountryListView(generics.ListAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.AllowAny]

    @method_decorator(cache_page(settings.CACHE_TTL))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CityViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]

    @method_decorator(cache_page(settings.CACHE_TTL))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(methods=['GET'], request=DistrictSerializer)
    @action(methods=['GET'], url_path='districts', detail=True)
    @method_decorator(cache_page(settings.CACHE_TTL))
    def get_districts(self, request, pk):
        districts = District.objects.filter(city_id=pk)
        serializer = DistrictSerializer(districts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
