from abc import abstractmethod, ABC
from ..models import Payment, ServiceType
from ...jobs.models import Job


class BaseServiceFulfillment(ABC):
    @abstractmethod
    def pre_fulfill(self, serializer) -> Payment:
        pass

    @abstractmethod
    def fulfill(self, payment: Payment):
        pass


class JobFeaturedFulfillment(BaseServiceFulfillment):
    def pre_fulfill(self, serializer) -> Payment:
        return serializer.save(amount=50000)

    def fulfill(self, payment: Payment):
        job_id = payment.meta_data['job_id']
        job = Job.objects.get(pk=job_id)
        job.status = Job.Status.PUBLISHED


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
