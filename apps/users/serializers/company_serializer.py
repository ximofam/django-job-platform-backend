import re

from rest_framework import serializers

from apps.locations.models import District, Address
from apps.locations.serializers import CountrySerializer
from apps.users.models import CompanyLocation, Company


class CompanyLocationSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField(read_only=True)
    address_id = serializers.SerializerMethodField(read_only=True)
    address_street = serializers.CharField(write_only=True, required=True)
    district = serializers.PrimaryKeyRelatedField(queryset=District.objects.all(), write_only=True, required=True)

    class Meta:
        model = CompanyLocation
        fields = ['id', 'address', 'label', 'is_primary', 'address_street', 'district', 'address_id']
        extra_kwargs = {
            'id': {'read_only': True},
            'address': {'read_only': True, 'required': True},
        }

    def get_address_id(self, obj):
        return obj.address.pk

    def get_address(self, obj):
        return obj.address.full_address

    def create(self, validated_data):
        address_street = validated_data.pop('address_street')
        district = validated_data.pop('district')

        address = Address.objects.create(street_address=address_street, district=district, city=district.city)
        return CompanyLocation.objects.create(address=address, **validated_data)


class CompanySimpleSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField(read_only=True)
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'type', 'employee_size', 'logo_url', 'country']

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None


class CompanySerializer(serializers.ModelSerializer):
    locations = CompanyLocationSerializer(many=True, read_only=True)
    new_locations = CompanyLocationSerializer(many=True, write_only=True, required=True)

    class Meta:
        model = Company
        fields = ['id', 'slug', 'status', 'type', 'employee_size', 'description', 'name', 'tax_code',
                  'country',
                  'new_locations', 'locations']
        extra_kwargs = {
            'description': {'required': False},
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'country': {'required': True},
            'status': {'read_only': True},
        }

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['country'] = CountrySerializer(instance.country).data
        response['logo_url'] = instance.logo.url if instance.logo else None
        return response


class CompanyUploadImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['logo']
        extra_kwargs = {
            'logo': {'required': True}
        }

    def to_representation(self, instance):
        return {
            'logo': instance.logo.url if instance.logo else None
        }

    def update(self, instance, validated_data):
        instance.avatar = validated_data['logo']
        instance.save(update_fields=['logo'])
        return instance
