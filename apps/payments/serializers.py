from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import ServiceType, Payment
from ..jobs.models import Job


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['service_type', 'metadata', 'method']

    def validate(self, attrs):
        service_type = attrs.get('service_type')
        metadata = attrs.get('metadata', {})
        request = self.context['request']

        if service_type == ServiceType.JOB_FEATURED:
            if not request.user.is_employer:
                raise PermissionDenied("Bạn không có quyền đăng tin")

            if 'job_id' not in metadata:
                raise serializers.ValidationError({
                    "metadata": "Bắt buộc phải truyền 'job_id' khi mua gói Tin nổi bật."
                })

            job = Job.objects.select_related('company', 'company__employer_profile').get(pk=metadata['job_id'])
            if not job:
                raise serializers.ValidationError({"job": "Job này không tồn tại"})

            if job.status != Job.Status.DRAFT:
                raise PermissionDenied("Bạn không được phép đăng tin này")

            if request.user.pk != job.company.employer_profile.pk:
                raise PermissionDenied("Bạn không được phép đăng tin này")

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        return Payment.objects.create(user=request.user, **validated_data)
