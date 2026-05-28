from abc import abstractmethod, ABC
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from ..models import Payment, ServiceType
from ..serializers import PaymentCreateSerializer
from ...jobs.models import Job


class BaseServiceFulfillment(ABC):
    @abstractmethod
    def pre_fulfill(self, **kwargs) -> Payment:
        pass

    @abstractmethod
    def fulfill(self, payment: Payment):
        pass


DAY = 24 * 60 * 60


class JobFeaturedFulfillment(BaseServiceFulfillment):
    _PROMOTION_PACKAGES = {
        'BASIC': {'seconds': settings.JOB_EXPIRE_SECONDS + DAY * 5, 'price': 199_000, 'score': 10},
        'STANDARD': {'seconds': settings.JOB_EXPIRE_SECONDS + DAY * 10, 'price': 399_000, 'score': 50},
        'PREMIUM': {'seconds': settings.JOB_EXPIRE_SECONDS + DAY * 20, 'price': 999_000, 'score': 100},
    }

    def pre_fulfill(self, request) -> Payment:
        data = request.data
        if "metadata" not in data:
            raise serializers.ValidationError("Thiếu metadata")

        package = JobFeaturedFulfillment._PROMOTION_PACKAGES[data['metadata']['package']]
        data['metadata']['package_data'] = package

        serializer = PaymentCreateSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        return serializer.save(amount=package['price'])

    def fulfill(self, payment: Payment):
        job_id = payment.metadata['job_id']
        package = payment.metadata['package_data']
        now = timezone.now()
        job = Job.objects.get(pk=job_id)
        job.status = Job.Status.PUBLISHED
        job.expired_at = now + timedelta(seconds=package['seconds'])
        job.published_at = now
        job.boost_score = package['score']
        job.save()


class FulfillmentFactory:
    _handlers = {
        ServiceType.JOB_FEATURED: JobFeaturedFulfillment,
    }

    @classmethod
    def get(cls, service_type) -> BaseServiceFulfillment:
        handler = cls._handlers.get(service_type)
        if not handler:
            raise ValueError(f'No fulfillment handler for service: {service_type}')
        return handler()
