from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.jobs import perms as job_perms
from apps.jobs.filters import JobFilter, JobSearchFilter, JobOrderingFilter, JobCursorPagination
from apps.jobs.models import Category, Job, CandidateCV
from apps.jobs.serializers import CategorySerializer, JobDetailsSerializer, JobSimpleSerializer, JobWriteSerializer
from apps.jobs.serializers.application_serializer import CandidateCVSerializer
from common import perms as common_perms


class CategoryTreeAPIView(generics.ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related('company', 'address__city', 'address__district', ).all()
    serializer_class = JobDetailsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filter_backends = [JobSearchFilter, DjangoFilterBackend, JobOrderingFilter]
    filterset_class = JobFilter
    ordering_fields = ['salary_min', 'salary_max', 'published_at']
    pagination_class = JobCursorPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'list':
            return queryset.filter(status=Job.Status.PUBLISHED)

        if self.action == 'retrieve':
            user = self.request.user
            if user.is_authenticated and hasattr(user, 'employer_profile'):
                return queryset.filter(
                    Q(status=Job.Status.PUBLISHED) |
                    Q(company=user.employer_profile.company)
                )
            return queryset.filter(status=Job.Status.PUBLISHED)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobDetailsSerializer
        if self.action == 'list':
            return JobSimpleSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return JobWriteSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        res = super().get_permissions()

        if self.action == 'create':
            res += [job_perms.CanPostJob()]
        elif self.action in ['job_publish', 'update', 'partial_update', 'destroy']:
            res += [common_perms.IsEmployer(), job_perms.IsJobOwner()]

        return res

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(company=user.employer_profile.company)

    @action(methods=['POST'], detail=True, url_path='publish')
    def job_publish(self, request, pk=None):
        job = self.get_object()

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


class CandidateCVViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = CandidateCV.objects.all()
    serializer_class = CandidateCVSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        res = super().get_permissions()
        if self.action in ['my_cvs', 'create']:
            res += [common_perms.IsCandidate()]

        return res

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(candidate_profile=user.candidate_profile)

    @action(methods=['GET'], url_path='my-cvs', detail=False, parser_classes=[parsers.MultiPartParser])
    def my_cvs(self, request):
        user = request.user
        cvs = CandidateCV.objects.filter(candidate_profile=user.candidate_profile)

        serializer = self.get_serializer(cvs, many=True)
        return Response(serializer.data)
