from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.jobs import views
from apps.jobs.views import CategoryTreeAPIView, CandidateCVViewSet

r = DefaultRouter()
r.register('jobs', views.JobViewSet)
r.register('cvs', CandidateCVViewSet)

urlpatterns = [
    path("api/", include(r.urls)),
    path("api/categories/", CategoryTreeAPIView.as_view(), name='category-tree'),
]
