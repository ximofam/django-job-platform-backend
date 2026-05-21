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


class CompanyBaseSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField(read_only=True)
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Company
        fields = [
            'id',
            'slug',
            'status',
            'name',
            'type',
            'employee_size',
            'description',
            'tax_code',
            'country',
            'logo_url',
        ]
        read_only_fields = ['id', 'slug', 'status', 'logo_url']

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None


class CompanySimpleSerializer(CompanyBaseSerializer):
    class Meta(CompanyBaseSerializer.Meta):
        fields = [
            'id',
            'name',
            'slug',
            'type',
            'employee_size',
            'logo_url',
            'country',
        ]


class CompanySerializer(CompanyBaseSerializer):
    locations = CompanyLocationSerializer(many=True, read_only=True)
    new_locations = CompanyLocationSerializer(many=True, write_only=True, required=True)

    class Meta(CompanyBaseSerializer.Meta):
        fields = CompanyBaseSerializer.Meta.fields + ['locations', 'new_locations']


class CompanyUpdateSerializer(CompanyBaseSerializer):
    class Meta(CompanyBaseSerializer.Meta):
        extra_kwargs = {
            'description': {'required': False},
            'country': {'required': False},
            'name': {'required': False},
            'type': {'required': False},
            'employee_size': {'required': False},
            'tax_code': {'read_only': True}
        }


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
