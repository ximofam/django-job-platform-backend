from rest_framework import serializers

from apps.jobs.models import CandidateCV


class CandidateCVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateCV
        fields = ['id', 'title', 'file']
        extra_kwargs = {
            'id': {'read_only': True},
        }
