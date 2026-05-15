from rest_framework import serializers

from apps.users.models import Country, Province


class CountrySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Country
        exclude = ['created_at', 'updated_at']

    @staticmethod
    def get_image(obj):
        if obj.image:
            return obj.image.url
        return None


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        exclude = ['created_at', 'updated_at']
