from rest_framework import serializers

from apps.jobs.models import CandidateCV, Application
from apps.jobs.serializers import JobDetailsSerializer, JobSimpleSerializer
from apps.users.serializers import UserDetailSerializer


class CandidateCVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateCV
        fields = ['id', 'title', 'file']
        extra_kwargs = {
            'id': {'read_only': True},
        }


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["job", "expected_salary", "cv_file"]
        extra_kwargs = {
            "expected_salary": {"required": True},
            "cv_file": {"required": True},
        }

    def validate_cv_file(self, cv):
        request = self.context["request"]
        candidate_profile = request.user.candidate_profile
        if cv and cv.candidate_profile != candidate_profile:
            raise serializers.ValidationError("CV không thuộc về ứng viên này.")
        return cv

    def validate(self, attrs):
        request = self.context["request"]
        candidate_profile = request.user.candidate_profile
        job = attrs["job"]

        if Application.objects.filter(candidate_profile=candidate_profile, job=job).exists():
            raise serializers.ValidationError("Bạn đã nộp hồ sơ cho công việc này rồi.")

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["candidate_profile"] = request.user.candidate_profile
        return super().create(validated_data)


class ApplicationSimpleSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job_title', 'expected_salary', 'status', 'applied_at']
        read_only_fields = fields

    def to_representation(self, instance):
        res = super().to_representation(instance)
        user = self.context['request'].user
        if user.is_employer:
            res['candidate_id'] = instance.candidate_profile.pk
            res['candidate_full_name'] = instance.candidate_profile.user.full_name

        return res


class ApplicationDetailsSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job_title', 'expected_salary', 'status', 'applied_at']
        read_only_fields = fields

    def to_representation(self, instance):
        res = super().to_representation(instance)
        res['cv_file_url'] = instance.cv_file.file.url if instance.cv_file.file else None

        user = self.context['request'].user
        if user.is_employer:
            res['candidate'] = UserDetailSerializer(instance.candidate_profile.user).data
        elif user.is_candidate:
            res['job'] = JobSimpleSerializer(instance.job).data

        return res


class ApplicationUpdateStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status']
        extra_kwargs = {
            'status': {'required': True}
        }

    def validate(self, attrs):
        status = attrs['status']
        if status == Application.Status.WITHDRAWN:
            raise serializers.ValidationError("Ứng viên đã rút hồ sơ")

        return attrs

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save(update_fields=['status'])
        return instance
