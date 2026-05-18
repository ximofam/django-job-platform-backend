from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.locations import views

r = DefaultRouter()
r.register("cities", views.CityViewSet)

urlpatterns = [
    path("api/", include(r.urls)),
    path("api/countries/", views.CountryListView.as_view(), name='list-countries')
]
