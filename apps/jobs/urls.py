from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.jobs import views
from apps.jobs.views import CategoryTreeAPIView, CandidateCVViewSet, ApplicationViewSet

r = DefaultRouter()
r.register('jobs', views.JobViewSet)
r.register('cvs', CandidateCVViewSet)
r.register('applications', ApplicationViewSet)

urlpatterns = [
    path("api/", include(r.urls)),
    path("api/categories/", CategoryTreeAPIView.as_view(), name='category-tree'),
]
