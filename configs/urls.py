"""
URL configuration for configs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
import oauth2_provider.views as oauth2_views

from apps.jobs.admin import JobStatisticsView
from common.views import ImageUploadAPIView, CustomTokenView

urlpatterns = [
    path('admin/job-stats/', JobStatisticsView.as_view(), name='admin_job_stats'),
    path('admin/', admin.site.urls),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/auth/token/', CustomTokenView.as_view(), name='token'),
    path('api/auth/revoke/', oauth2_views.RevokeTokenView.as_view(), name='revoke-token'),
    path('api/auth/introspect/', oauth2_views.IntrospectTokenView.as_view(), name='introspect'),
    path('api/upload-image/', ImageUploadAPIView.as_view(), name='upload-image'),
    path('', include('apps.locations.urls')),
    path('', include('apps.users.urls')),
    path('', include('apps.jobs.urls')),
    path('', include('apps.payments.urls'))
]
