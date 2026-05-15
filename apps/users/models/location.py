from cloudinary.models import CloudinaryField

from common.models import BaseModel
from django.db import models


class Country(BaseModel):
    code = models.CharField(max_length=10, unique=True, null=False)
    name = models.CharField(max_length=100, null=False)
    image = CloudinaryField("flags", folder="countries/flags/", null=True, blank=True)

    class Meta:
        ordering = ['code']


class Province(BaseModel):
    code = models.CharField(max_length=10, unique=True, null=False)
    codename = models.CharField(max_length=100, unique=True, null=False, default='vietnam')
    name = models.CharField(max_length=100, null=False)
