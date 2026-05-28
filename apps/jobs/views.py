from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.jobs import perms as job_perms, perms
from apps.jobs.filters import JobFilter, JobSearchFilter, JobOrderingFilter, JobCursorPagination
from apps.jobs.models import Category, Job, CandidateCV, Application
from apps.jobs.serializers import CategorySerializer, JobDetailsSerializer, JobSimpleSerializer, JobWriteSerializer, \
    ApplicationDetailsSerializer, ApplicationCreateSerializer, ApplicationSimpleSerializer
from apps.jobs.serializers.application_serializer import CandidateCVSerializer, ApplicationUpdateStatusSerializer
from apps.notifications.tasks import send_gotify_notification
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

        now = timezone.now()
        expires_at = now + timedelta(seconds=settings.JOB_EXPIRE_SECONDS)
        job.status = Job.Status.PUBLISHED
        job.published_at = now
        job.expired_at = expires_at
        job.save()

        return Response({'id': job.pk}, status=status.HTTP_200_OK)


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

    @action(methods=['GET'], url_path='my', detail=False, parser_classes=[parsers.MultiPartParser])
    def my_cvs(self, request):
        user = request.user
        cvs = CandidateCV.objects.filter(candidate_profile=user.candidate_profile)

        serializer = self.get_serializer(cvs, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.RetrieveAPIView, generics.ListAPIView):
    queryset = Application.objects.all()
    permission_classes = [permissions.IsAuthenticated, perms.IsEmployerOrCandidate]
    serializer_class = ApplicationDetailsSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        elif self.action == 'list':
            return ApplicationSimpleSerializer
        elif self.action == 'retrieve':
            return ApplicationDetailsSerializer
        elif self.action == 'update_status':
            return ApplicationUpdateStatusSerializer

        return super().get_serializer_class()

    def get_permissions(self):
        res = super().get_permissions()

        if self.action == 'create':
            return res + [common_perms.IsCandidate()]

        if self.action == 'update_status':
            return res + [common_perms.IsEmployer()]

        return res

    def get_queryset(self):
        user = self.request.user

        if user.is_employer:
            return Application.objects.filter(
                job__company_id=user.employer_profile.company_id
            ).select_related('candidate_profile', 'candidate_profile__user', 'job', 'cv_file')

        if user.is_candidate:
            return Application.objects.filter(
                candidate_profile=user.candidate_profile
            ).select_related('job')

        return Application.objects.none()

    @action(methods=['PATCH'], url_path='status', detail=True)
    def update_status(self, request, pk):
        application = self.get_object()
        old_status = getattr(application, 'status', None)

        serializer = ApplicationUpdateStatusSerializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_application = serializer.save()

        new_status = updated_application.status

        candidate_id = updated_application.candidate_profile.pk
        job = updated_application.job
        job_title = job.title if hasattr(updated_application, 'job') else "Vị trí bạn ứng tuyển"
        company_name = job.company.name

        message = (f"Hồ sơ ứng tuyển cho vị trí {job_title} của công ty {company_name} của bạn đã được duyệt.\n"
                   f"Từ {old_status} -> {new_status} :V")

        send_gotify_notification.delay(
            user_id=candidate_id,
            title="Cập nhật trạng thái hồ sơ",
            message=message,
            priority=6
        )

        return Response(
            data=ApplicationSimpleSerializer(updated_application, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
