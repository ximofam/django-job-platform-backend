from cloudinary.models import CloudinaryField
from django.db import models

from common.models import BaseModel


class Country(BaseModel):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=255)
    image = CloudinaryField("flags", folder="countries/flags/", null=True, blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.name


class City(BaseModel):
    name = models.CharField(max_length=100, verbose_name="Tên thành phố")
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã thành phố")

    class Meta:
        verbose_name = "Thành phố"
        verbose_name_plural = "Thành phố"
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(BaseModel):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="districts", verbose_name="Thành phố")
    name = models.CharField(max_length=100, verbose_name="Tên quận/huyện")
    code = models.CharField(max_length=20, verbose_name="Mã quận/huyện")

    class Meta:
        verbose_name = "Quận/Huyện"
        verbose_name_plural = "Quận/Huyện"
        ordering = ["name"]
        unique_together = ("city", "code")

    def __str__(self):
        return f"{self.name}, {self.city.name}"


class Address(BaseModel):
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="addresses", verbose_name="Thành phố")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="addresses",
                                 verbose_name="Quận/Huyện")
    street_address = models.CharField(max_length=255, verbose_name="Địa chỉ đường/số nhà",
                                      help_text="Ví dụ: 123 Nguyễn Huệ")

    class Meta:
        verbose_name = "Địa chỉ"
        verbose_name_plural = "Địa chỉ"

    def __str__(self):
        parts = [self.street_address, self.district.name, self.city.name]
        return ", ".join(parts)

    @property
    def full_address(self) -> str:
        return str(self)
