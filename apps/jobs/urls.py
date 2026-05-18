from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.jobs.views import CategoryTreeAPIView

r = DefaultRouter()

urlpatterns = [
    path("api/", include(r.urls)),
    path("api/categories/", CategoryTreeAPIView.as_view(), name='category-tree'),
]
