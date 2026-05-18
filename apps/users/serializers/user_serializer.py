from django.db import transaction
from rest_framework import serializers

from apps.users.models import User, CandidateProfile, Company, EmployerProfile, Education, Experience, CompanyLocation
from .company_serializer import CompanySerializer, CountrySerializer, CompanyLocationSerializer
from ...locations.models import Address


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'gender', 'country']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.assign_role(User.Role.CANDIDATE)

        CandidateProfile.objects.create(user=user)
        return user


class EmployerCreateSerializer(UserCreateSerializer):
    company = CompanySerializer(write_only=True)

    class Meta:
        model = User
        fields = UserCreateSerializer.Meta.fields + ['company']

    @transaction.atomic
    def create(self, validated_data):
        company_data = validated_data.pop('company')
        company = None

        if company_data:
            locations_data = company_data.pop('new_locations', [])
            company = Company.objects.create(**company_data)

            for location_data in locations_data:
                district = location_data.pop('district')
                address = Address.objects.create(
                    street_address=location_data.pop('address_street'),
                    district=district,
                    city=district.city,
                )
                CompanyLocation.objects.create(address=address, company=company, **location_data)

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.role = User.Role.EMPLOYER
        user.save()

        EmployerProfile.objects.create(user=user, company=company)
        return user


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        exclude = ['candidate_profile', 'created_at', 'updated_at']
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "end_date": "Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu."
            })

        return data


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        exclude = ['candidate_profile', 'created_at', 'updated_at']
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "end_date": "Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu."
            })

        return data


class CandidateProfileSerializer(serializers.ModelSerializer):
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateProfile
        fields = ['bio', 'educations', 'experiences']


class EmployerProfileSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = EmployerProfile
        fields = ['approved_by', 'approved_at', 'company']


class UserDetailSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'avatar', 'gender', 'date_of_birth', 'address',
                  'profile',
                  'country']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['avatar'] = instance.avatar.url if instance.avatar else None

        request = self.context.get('request')
        is_owner = request and request.user == instance

        profile_obj = instance.profile

        if isinstance(profile_obj, CandidateProfile):
            response['profile'] = CandidateProfileSerializer(profile_obj).data

        elif isinstance(profile_obj, EmployerProfile):
            if profile_obj.status != EmployerProfile.Status.APPROVED:
                return None

            profile_res = EmployerProfileSerializer(profile_obj).data

            if not is_owner:
                profile_res.pop('approved_by')
                profile_res.pop('approved_at')

            response['profile'] = profile_res

        else:
            response['profile'] = None

        return response


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'address', 'country']


class UserUploadImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar']
        extra_kwargs = {
            'avatar': {'required': True}
        }

    def to_representation(self, instance):
        return {
            "avatar": instance.avatar.url if instance.avatar else None
        }

    def update(self, instance, validated_data):
        instance.avatar = validated_data['avatar']
        instance.save(update_fields=['avatar'])
        return instance
