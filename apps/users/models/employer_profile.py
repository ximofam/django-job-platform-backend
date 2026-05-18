from autoslug import AutoSlugField
from cloudinary.models import CloudinaryField

from apps.locations.models import Country, Address
from apps.users.models import User
from common.models import BaseModel
from django.db import models

from common.utils import slugify


class EmployerProfile(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        DENIED = 'DENIED', 'Denied'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employer_profile", primary_key=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    company = models.OneToOneField('Company', on_delete=models.CASCADE, related_name="employer_profile")
    approved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="approved_employers")
    approved_at = models.DateTimeField(null=True, blank=True)


class Company(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        DENIED = 'DENIED', 'Denied'

    class Type(models.TextChoices):
        PRODUCT = 'PRODUCT', 'Công ty sản phẩm'
        OUTSOURCE = 'OUTSOURCE', 'Gia công'
        STARTUP = 'STARTUP', 'Khởi nghiệp'
        AGENCY = 'AGENCY', 'Agency'
        FOREIGN = 'FOREIGN', 'Công ty nước ngoài / liên doanh'
        STATE_OWNED = 'STATE_OWNED', 'Doanh nghiệp nhà nước'
        OTHER = 'OTHER', 'Khác'

    class EmployeeSize(models.TextChoices):
        SMALL = 'SMALL', '1 - 50'
        MEDIUM = 'MEDIUM', '51 - 200'
        LARGE = 'LARGE', '201 - 500'
        VERY_LARGE = 'VERY_LARGE', '501 - 1000'
        ENTERPRISE = 'ENTERPRISE', '1000+'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    logo = CloudinaryField(null=True, blank=True)
    name = models.CharField(max_length=150, verbose_name='Tên công ty')
    slug = AutoSlugField(populate_from="name", unique=True, slugify=slugify, always_update=False)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.OTHER)
    employee_size = models.CharField(max_length=20, choices=EmployeeSize.choices)
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, related_name='companies')
    description = models.TextField(null=True, blank=True, verbose_name='Sơ lược về công ty')
    tax_code = models.CharField(max_length=20, unique=True, null=False, verbose_name='Mã số thuế')

    def __str__(self):
        return self.name


class CompanyLocation(BaseModel):
    class Label(models.TextChoices):
        HEADQUARTERS = "HEADQUARTERS", "Trụ sở chính",
        BRANCH = "BRANCH", "Chi nhánh",

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="locations")
    address = models.ForeignKey('locations.Address', on_delete=models.PROTECT)
    label = models.CharField(max_length=50, choices=Label.choices, default=Label.BRANCH)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('company', 'address')
