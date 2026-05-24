from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.notifications import views

router = DefaultRouter()

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/gotify/basic-token/', views.GotifyView.as_view(), name='client-token')
]
