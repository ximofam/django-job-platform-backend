from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users import views
from apps.users.views import CountryViewSet, UserViewSet, CompanyViewSet

r = DefaultRouter()
r.register("users", UserViewSet)
r.register("companies", CompanyViewSet)

urlpatterns = [
    path("api/", include(r.urls)),
    path('api/auth/register/candidate/', views.CandidateRegisterView.as_view(), name='register-candidate'),
    path('api/auth/register/employer/', views.EmployerRegisterView.as_view(), name='register-employer'),
    path('api/countries/', views.CountryViewSet.as_view(), name='get-all-countries'),
    path('api/provinces/', views.ProvinceViewSet.as_view(), name='get-all-provinces'),
]
