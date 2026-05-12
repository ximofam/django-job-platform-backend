from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.users.views import CountryViewSet

r = DefaultRouter()
r.register("countries", CountryViewSet)

urlpatterns = [
    path("api/", include(r.urls))
]
