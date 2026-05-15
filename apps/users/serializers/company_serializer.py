from rest_framework import serializers

from apps.users.models import CompanyLocation, Company, Country
from .location_serializer import ProvinceSerializer, CountrySerializer


class CompanyLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyLocation
        fields = ['id', 'province', 'address']
        extra_kwargs = {
            'id': {'read_only': True},
            'province': {'required': True},
            'address': {'required': True},
        }

    def to_representation(self, instance):
        res = super().to_representation(instance)

        res['province'] = ProvinceSerializer(instance.province).data

        return res


class CompanySerializer(serializers.ModelSerializer):
    locations = CompanyLocationSerializer(many=True, read_only=True)
    location = CompanyLocationSerializer(write_only=True, required=True)
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'slug', 'status', 'logo', 'type', 'employee_size', 'description', 'name', 'tax_code', 'country',
                  'location', 'locations']
        extra_kwargs = {
            'description': {'required': False},
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'country': {'required': True}
        }

    def to_representation(self, instance):
        response = super().to_representation(instance)

        response['country'] = CountrySerializer(instance.country).data

        return response
