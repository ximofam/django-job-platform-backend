from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.users.models import User, Company, CompanyLocation
from apps.users.perms import IsCompanyOwner
from common import perms as common_perms
from apps.users.serializers import UserCreateSerializer, EmployerCreateSerializer, \
    UserUpdateSerializer, UserDetailSerializer, EducationSerializer, ExperienceSerializer, CompanySerializer, \
    CompanyLocationSerializer, UserUploadImageSerializer, CompanyUploadImageSerializer, CompanySimpleSerializer


class CandidateRegisterView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Đăng ký ứng viên thành công."},
            status=status.HTTP_201_CREATED
        )


class EmployerRegisterView(generics.CreateAPIView):
    serializer_class = EmployerCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Đăng ký nhà tuyển dụng thành công."},
            status=status.HTTP_201_CREATED
        )


class UserViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserDetailSerializer
    lookup_field = 'username'
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ['current_user', 'upload_my_avatar']:
            return [permissions.IsAuthenticated()]
        if self.action in ['add_my_education', 'add_my_experience']:
            return [common_perms.IsCandidate()]
        return super().get_permissions()

    @extend_schema(methods=['PATCH'], request=UserUpdateSerializer)
    @action(methods=['GET', 'PATCH'], url_path='me', detail=False)
    def current_user(self, request):
        user = request.user

        if request.method == 'PATCH':
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(UserDetailSerializer(user).data, status=status.HTTP_200_OK)

        return Response(UserDetailSerializer(user, context={"request": request}).data)

    @extend_schema(request=UserUploadImageSerializer)
    @action(methods=['PATCH'], url_path='me/upload-avatar', detail=False)
    def upload_my_avatar(self, request):
        serializer = UserUploadImageSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=EducationSerializer)
    @action(methods=['POST'], url_path='me/educations', detail=False)
    def add_my_education(self, request):
        serializer = EducationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(candidate_profile=request.user.candidate_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=ExperienceSerializer)
    @action(methods=['POST'], url_path='me/experiences', detail=False)
    def add_my_experience(self, request):
        serializer = ExperienceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(candidate_profile=request.user.candidate_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CompanyViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.ListAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        base_qs = Company.objects.filter(status=Company.Status.APPROVED).select_related('country')

        if self.action in ['retrieve', 'update', 'partial_update']:
            return base_qs.prefetch_related(
                Prefetch('locations', queryset=CompanyLocation.objects.select_related(
                    'address__district',
                    'address__city',
                ))
            )

        return base_qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanySerializer

        if self.action == 'list':
            return CompanySimpleSerializer

        return super().get_serializer_class()

    def get_permissions(self):
        res = super().get_permissions()

        if self.action in ['add_location', 'upload_logo']:
            return res + [IsCompanyOwner()]

        return res

    @extend_schema(request=CompanyLocationSerializer)
    @action(methods=['POST', 'GET'], url_path='locations', detail=True)
    def locations(self, request, slug):
        if request.method == 'GET':
            company = self.get_object()
            locations = company.locations.select_related(
                'address__district',
                'address__city').all()

            serializer = CompanyLocationSerializer(locations, many=True)
            return Response(serializer.data)

        serializer = CompanyLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(company=self.get_object())
        return Response(data="Tạo thành công vị trí cho công ty", status=status.HTTP_201_CREATED)

    @extend_schema(request=CompanyUploadImageSerializer)
    @action(methods=['PATCH'], url_path='upload-logo', detail=True)
    def upload_logo(self, request, slug):
        serializer = CompanyUploadImageSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
