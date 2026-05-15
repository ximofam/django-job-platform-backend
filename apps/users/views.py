from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action, permission_classes
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from apps.users.models import Country, User, Company, Province
from apps.users.perms import IsCandidate, IsCompanyOwner
from apps.users.serializers import CountrySerializer, UserCreateSerializer, EmployerCreateSerializer, \
    UserUpdateSerializer, UserDetailSerializer, EducationSerializer, ExperienceSerializer, CompanySerializer, \
    ProvinceSerializer, CompanyLocationSerializer


class CountryViewSet(generics.ListAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


class ProvinceViewSet(generics.ListAPIView):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer
    permission_classes = [AllowAny]


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
    parser_classes = [MultiPartParser]

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
    serializer_class = [UserDetailSerializer]
    parser_classes = [MultiPartParser, JSONParser]
    lookup_field = 'username'

    @extend_schema(methods=['GET'])
    @extend_schema(methods=['PATCH'], request=UserUpdateSerializer, )
    @action(methods=['GET', 'PATCH'], url_path='me', detail=False, permission_classes=[permissions.IsAuthenticated])
    def current_user(self, request):
        user = request.user

        if request.method == 'PATCH':
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response_serializer = UserDetailSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        serializer = UserDetailSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=EducationSerializer)
    @action(methods=['POST'], url_path='me/educations', detail=False, permission_classes=[IsCandidate])
    def add_my_education(self, request):
        serializer = EducationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(candidate_profile=request.user.candidate_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(request=ExperienceSerializer, )
    @action(methods=['POST'], url_path='me/experiences', detail=False, permission_classes=[IsCandidate])
    def add_my_experience(self, request):
        serializer = ExperienceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(candidate_profile=request.user.candidate_profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CompanyViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.ListAPIView):
    queryset = Company.objects.filter(status=Company.Status.APPROVED)
    serializer_class = CompanySerializer
    lookup_field = 'slug'
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description']

    def get_permissions(self):
        res = [permissions.IsAuthenticatedOrReadOnly()]

        if self.action == 'add_location':
            return res + [IsCompanyOwner()]

        return res

    @extend_schema(request=CompanyLocationSerializer)
    @action(methods=['POST'], url_path='locations', detail=True)
    def add_location(self, request, slug):
        serializer = CompanyLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(company=self.get_object())
        return Response(data="Tạo thành công vị trí cho công ty", status=status.HTTP_201_CREATED)
