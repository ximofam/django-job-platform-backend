from rest_framework import serializers

from apps.locations.models import Country, City, District, Address


class CountrySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Country
        fields = ['id', 'code', 'name', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'code', 'name']


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'code', 'name']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street_address', 'city', 'district']
        extra_kwargs = {
            'id': {'read_only': True}
        }
