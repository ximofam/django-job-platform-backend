from autoslug import AutoSlugField
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models import Q

from common.models import BaseModel, SoftDeleteModel
from common.utils import slugify


class Country(SoftDeleteModel):
    code = models.CharField(max_length=10, null=False)
    name = models.CharField(max_length=100, null=False)
    image = CloudinaryField("countries/flags", null=True)

    class Meta:
        ordering = ['code']
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_country_code_active'
            )
        ]


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = "MALE", "Nam"
        FEMALE = "FEMALE", "Nữ"

    class Role(models.TextChoices):
        CANDIDATE = 'CANDIDATE', 'ứng viên'
        EMPLOYER = 'EMPLOYER', 'nhà tuyển dụng'
        ADMIN = 'ADMIN', 'quản trị viên'

    email = models.EmailField(max_length=100, null=False, blank=False, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    avatar = CloudinaryField("users/avatars", null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, related_name='users')

    def assign_role(self, role):
        valid_roles = [choice[0] for choice in User.Role.choices]
        if role not in valid_roles:
            return False

        self.role = role
        self.save(update_fields=['role'])

        group = Group.objects.get(name=role)
        self.groups.clear()
        self.groups.add(group)
        return True

    @property
    def is_candidate(self):
        return self.role == User.Role.CANDIDATE

    @property
    def is_employer(self):
        return self.role == User.Role.EMPLOYER

    @property
    def is_admin(self):
        return self.role == User.Role.ADMIN


class CandidateProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile", primary_key=True)
    bio = models.TextField(null=True, blank=True)


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


class Company(SoftDeleteModel):
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

    logo = CloudinaryField("companies/logo", null=True)
    name = models.CharField(max_length=150, verbose_name='Tên công ty')
    slug = AutoSlugField(populate_from="name", unique=True, slugify=slugify, always_update=False)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.OTHER)
    employee_size = models.CharField(max_length=20, choices=EmployeeSize.choices)
    address = models.CharField(max_length=255, verbose_name='Địa chỉ công ty')
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, related_name='companies')
    description = models.TextField(null=True, blank=True, verbose_name='Sơ lược về công ty')
    tax_code = models.CharField(max_length=20, null=True, blank=True, verbose_name='Mã số thuế')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tax_code'],
                condition=Q(deleted_at__isnull=True),
                name='uq_company_tax_code_active'
            )
        ]

    def __str__(self):
        return self.name


class Experience(BaseModel):
    candidate_profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=150, verbose_name='Tên công ty')
    position = models.CharField(max_length=150, verbose_name='Chức vụ')
    description = models.TextField(null=True, blank=True, verbose_name='Mô tả công việc')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.position} tại {self.company}"


class Education(BaseModel):
    class Degree(models.TextChoices):
        HIGH_SCHOOL = 'HIGH_SCHOOL', 'THPT'
        COLLEGE = 'COLLEGE', 'Cao đẳng'
        BACHELOR = 'BACHELOR', 'Đại học'
        MASTER = 'MASTER', 'Thạc sĩ'
        PHD = 'PHD', 'Tiến sĩ'
        OTHER = 'OTHER', 'Khác'

    candidate_profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='educations')
    school = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    major = models.CharField(max_length=150, null=False, blank=False, verbose_name='Chuyên ngành')
    degree = models.CharField(max_length=20, null=False, choices=Degree.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.degree} - {self.major} tại {self.school}"
