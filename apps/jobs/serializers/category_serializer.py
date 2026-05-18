from rest_framework import serializers

from apps.jobs.models import Category


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'children']

    def get_children(self, obj):
        if obj.parent_id is not None:
            return []

        children = obj.children.all()

        if not children:
            return []

        return CategorySerializer(children, many=True).data
