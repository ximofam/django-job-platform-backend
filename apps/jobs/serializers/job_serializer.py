from django.db import transaction
from rest_framework import serializers
from django.utils import timezone

from apps.jobs.models import Job
from apps.locations.models import Address
from apps.locations.serializers import AddressSerializer
from apps.users.models import Company
from apps.users.serializers import CompanySerializer


class CompanySimpleSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'logo_url']
        read_only_fields = fields

    def get_logo_url(self, obj):
        return obj.logo.url if obj.logo else None


class JobBaseSerializer(serializers.ModelSerializer):
    salary = serializers.SerializerMethodField()
    company = CompanySimpleSerializer()
    address = serializers.CharField(source='address.full_address')

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'company',
            'address',
            'salary',
            'published_at',
        ]

    def get_salary(self, obj) -> dict | None:
        if obj.salary_min is None and obj.salary_max is None:
            return None

        return {
            'min': obj.salary_min,
            'max': obj.salary_max,
            'currency': obj.salary_currency,
            'display': self._format_salary(obj),
        }

    @staticmethod
    def _format_salary(obj) -> str:
        currency = obj.salary_currency

        if obj.salary_min is not None and obj.salary_max is not None:
            return f"{obj.salary_min:,.0f} - {obj.salary_max:,.0f} {currency}"

        if obj.salary_min is not None:
            return f"Từ {obj.salary_min:,.0f} {currency}"

        if obj.salary_max is not None:
            return f"Đến {obj.salary_max:,.0f} {currency}"

        return "Thỏa thuận"


class JobSimpleSerializer(JobBaseSerializer):
    class Meta(JobBaseSerializer.Meta):
        fields = JobBaseSerializer.Meta.fields


class JobDetailsSerializer(JobBaseSerializer):
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)
    is_expired = serializers.SerializerMethodField()
    company = CompanySerializer()

    class Meta(JobBaseSerializer.Meta):
        fields = JobBaseSerializer.Meta.fields + [
            'employment_type',
            'employment_type_display',
            'status',
            'status_display',
            'experience_level',
            'experience_level_display',
            'requirements',
            'benefit',
            'salary_min',
            'salary_max',
            'salary_currency',
            'is_expired'
        ]
        read_only_fields = fields

    @staticmethod
    def get_is_expired(obj) -> bool:
        return bool(obj.expired_at and obj.expired_at < timezone.now())


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

    def to_representation(self, instance):
        return {
            'id': instance.pk
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


class JobStatisticSimpleSerializer(serializers.ModelSerializer):
    application_count = serializers.IntegerField(source='annotated_app_count', read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'title', 'status', 'published_at', 'expired_at', 'application_count']
