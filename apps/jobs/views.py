from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import generics, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.jobs import perms as job_perms
from apps.jobs.models import Category, Job
from apps.jobs.search import PostgresFullTextSearchFilter
from apps.jobs.serializers import CategorySerializer, JobDetailsSerializer, JobSimpleSerializer, JobCreateSerializer
from common import perms as common_perms


class CategoryTreeAPIView(generics.ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class JobViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView, generics.CreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobDetailsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [PostgresFullTextSearchFilter]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobDetailsSerializer

        if self.action == 'list':
            return JobSimpleSerializer

        if self.action == 'create':
            return JobCreateSerializer

        return super().get_serializer_class()

    def get_permissions(self):
        res = super().get_permissions()

        if self.action == 'create':
            return res + [common_perms.IsEmployer()]

        if self.action in ['job_publish', 'update', 'partial_update', 'destroy']:
            return res + [common_perms.IsEmployer(), job_perms.IsJobOwner()]

        return res

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(company=user.employer_profile.company)

    @action(methods=['POST'], detail=True, url_path='publish')
    def job_publish(self, request, pk=None):
        job = self.get_object()

        if job.company != request.user.employer_profile.company:
            return Response(
                {'detail': 'Bạn không có quyền publish job này.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if job.status != Job.Status.DRAFT:
            return Response(
                {'detail': f'Không thể publish job ở trạng thái "{job.status}".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        boost_package = request.data.get('boost')

        if boost_package:
            return self._publish_with_boost(request, job, boost_package)

        return self._publish_free(job)

    def _publish_free(self, job):
        expires_at = timezone.now() + timedelta(days=settings.JOB_EXPIRE_DAYS)
        job.status = Job.Status.PUBLISHED
        job.expired_at = expires_at
        job.save(update_fields=['status', 'expired_at'])

        return Response(
            JobDetailsSerializer(job).data,
            status=status.HTTP_200_OK
        )

    def _publish_with_boost(self, request, job, boost_data):
        pass
