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


class CityViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(methods=['GET'], request=DistrictSerializer)
    @action(methods=['GET'], url_path='districts', detail=True)
    def get_districts(self, request, pk):
        districts = District.objects.filter(city_id=pk)
        serializer = DistrictSerializer(districts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
