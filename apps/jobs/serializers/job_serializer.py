from django.db import transaction
from rest_framework import serializers

from apps.jobs.models import Job
from apps.locations.models import Address
from apps.locations.serializers import AddressSerializer
from apps.users.serializers import CompanySimpleSerializer


class JobSimpleSerializer(serializers.ModelSerializer):
    salary_range = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'salary_range']

    def get_salary_range(self, obj) -> dict | None:
        if obj.salary_min is None and obj.salary_max is None:
            return None
        return {
            'min': obj.salary_min,
            'max': obj.salary_max,
            'currency': obj.salary_currency,
            'display': self._format_salary(obj),
        }

    def get_logo_url(self, obj):
        return obj.company.logo.url if obj.company.logo else None

    def _format_salary(self, obj) -> str:
        cur = obj.salary_currency
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min:,.0f} - {obj.salary_max:,.0f} {cur}"
        if obj.salary_min:
            return f"Từ {obj.salary_min:,.0f} {cur}"
        if obj.salary_max:
            return f"Đến {obj.salary_max:,.0f} {cur}"
        return "Thỏa thuận"


class JobDetailsSerializer(JobSimpleSerializer):
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


class FlexibleAddressField(serializers.Field):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            serializer = AddressSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data

        elif isinstance(data, (int, str)) and str(data).isdigit():
            try:
                return Address.objects.get(pk=data)
            except Address.DoesNotExist:
                raise serializers.ValidationError("Địa chỉ này không tồn tại.")

        raise serializers.ValidationError(
            "Định dạng không hợp lệ. Vui lòng truyền ID địa chỉ hoặc object thông tin địa chỉ."
        )

    def to_representation(self, value):
        return AddressSerializer(value).data


class JobWriteSerializer(serializers.ModelSerializer):
    address = FlexibleAddressField(required=True)

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

    @transaction.atomic
    def create(self, validated_data):
        address_data = validated_data.pop('address')
        if isinstance(address_data, dict):
            address_instance = Address.objects.create(**address_data)
        else:
            address_instance = address_data

        validated_data['address'] = address_instance
        validated_data['status'] = Job.Status.DRAFT
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'address' in validated_data:
            address_data = validated_data.pop('address')

            if isinstance(address_data, dict):
                new_address = Address.objects.create(**address_data)
                instance.address = new_address
            else:
                instance.address = address_data

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
