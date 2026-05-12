from rest_framework import serializers

from apps.users.models import Country, User


class CountrySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ['id', 'code', 'name', 'image']

    @staticmethod
    def get_image(obj):
        if obj.image:
            return obj.image.url
        return None


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
