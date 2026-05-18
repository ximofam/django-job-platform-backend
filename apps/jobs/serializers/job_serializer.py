from rest_framework import serializers

from apps.jobs.models import Job
from apps.users.serializers import CompanySimpleSerializer


class JobSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'description']


class JobDetailsSerializer(serializers.ModelSerializer):
    company = CompanySimpleSerializer(read_only=True)
    address = serializers.SerializerMethodField()

    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)

    is_expired = serializers.SerializerMethodField()
    salary_range = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id',
            'employment_type', 'employment_type_display',
            'status', 'status_display',
            'experience_level', 'experience_level_display',
            'title', 'description', 'requirements', 'benefit',
            'salary_min', 'salary_max', 'salary_currency', 'salary_range',
            'is_expired', 'company', 'address',
        ]
        read_only_fields = fields

    def get_address(self, obj) -> str:
        return obj.address.full_address

    def get_is_expired(self, obj) -> bool:
        from django.utils import timezone
        return bool(obj.expired_at and obj.expired_at < timezone.now())

    def get_salary_range(self, obj) -> dict | None:
        if obj.salary_min is None and obj.salary_max is None:
            return None
        return {
            'min': obj.salary_min,
            'max': obj.salary_max,
            'currency': obj.salary_currency,
            'display': self._format_salary(obj),
        }

    def _format_salary(self, obj) -> str:
        cur = obj.salary_currency
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min:,.0f} - {obj.salary_max:,.0f} {cur}"
        if obj.salary_min:
            return f"Từ {obj.salary_min:,.0f} {cur}"
        if obj.salary_max:
            return f"Đến {obj.salary_max:,.0f} {cur}"
        return "Thỏa thuận"


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'company', 'category', 'address', 'employment_type', 'experience_level', 'title', 'description',
                  'requirements', 'benefit', 'salary_min', 'salary_max', 'salary_currency']
        extra_kwargs = {
            'employment_type': {'required': False},
            'salary_currency': {'required': False},
            'experience_level': {'allow_null': True, 'required': False},
            'company': {'read_only': True},
            'id': {'read_only': True},
        }

    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        if salary_min is not None and salary_max is not None:
            if salary_min > salary_max:
                raise serializers.ValidationError({
                    'salary_min': 'Lương tối thiểu không được lớn hơn lương tối đa.'
                })
        return attrs

    def create(self, validated_data):
        validated_data['status'] = Job.Status.DRAFT
        return super().create(validated_data)
