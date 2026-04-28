from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models import BaseModel as SoftDeleteModel


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    EMPLOYER = 'employer', 'Employer'
    CANDIDATE = 'candidate', 'Candidate'


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices)


class Country(SoftDeleteModel):
    code = models.CharField(max_length=10, null=False, unique=True)
    name = models.CharField(max_length=100, null=False)
    image = CloudinaryField(null=True)


class UserProfile(BaseModel):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    avatar = CloudinaryField(null=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_list'
    )

    class Meta:
        abstract = True


class AdminProfile(UserProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")


class CandidateProfile(UserProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile")


class EmployerProfile(UserProfile):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employer_profile")
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="employer_profiles")


class Company(SoftDeleteModel):
    TYPE_CHOICES = [
        ('foreign_100', '100% vốn nước ngoài'),
        ('individual', 'Cá nhân'),
        ('multinational', 'Công ty đa quốc gia'),
        ('joint_stock', 'Cổ phần'),
        ('state_owned', 'Nhà nước'),
        ('llc', 'Trách nhiệm hữu hạn'),
    ]

    EMPLOYEE_SIZE_CHOICES = [
        ('lt10', 'Ít hơn 10'),
        ('10_24', '10-24'),
        ('25_99', '25-99'),
        ('100_499', '100-499'),
        ('500_999', '500-999'),
        ('1000_4999', '1.000-4.999'),
        ('5000_9999', '5.000-9.999'),
        ('10000_19999', '10.000-19.999'),
        ('20000_49999', '20.000-49.999'),
        ('gt50000', 'Hơn 50.000'),
    ]

    logo = CloudinaryField(null=True)
    name = models.CharField(max_length=150, verbose_name='Tên công ty')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    employee_size = models.CharField(max_length=20, choices=EMPLOYEE_SIZE_CHOICES)
    address = models.CharField(max_length=255, verbose_name='Địa chỉ công ty')
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, related_name='companies')
    description = models.TextField(null=True, blank=True, verbose_name='Sơ lược về công ty')
    tax_code = models.CharField(max_length=20, null=True, blank=True, verbose_name='Mã số thuế')


class Experience(BaseModel):
    candidate_profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=150, verbose_name='Tên công ty')
    position = models.CharField(max_length=150, verbose_name='Chức vụ')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name='Mô tả công việc')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.position} tại {self.company}"


class University(SoftDeleteModel):
    STATUS_CHOICES = [
        ('approved', 'Đã duyệt'),
        ('pending', 'Chờ duyệt'),
        ('rejected', 'Từ chối'),
    ]

    name = models.CharField(max_length=200, unique=True, verbose_name='Tên trường')
    short_name = models.CharField(max_length=50, null=True, blank=True, verbose_name='Tên viết tắt')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL, related_name="universities")
    city = models.CharField(max_length=255, blank=True)
    logo = CloudinaryField(null=True)

    def __str__(self):
        return self.name


class Education(BaseModel):
    DEGREE_CHOICES = [
        ('high_school', 'THPT'),
        ('college', 'Cao đẳng'),
        ('bachelor', 'Đại học'),
        ('master', 'Thạc sĩ'),
        ('phd', 'Tiến sĩ'),
        ('other', 'Khác'),
    ]

    candidate_profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name='educations')
    university = models.ForeignKey(University, on_delete=models.PROTECT, related_name='educations')
    major = models.CharField(max_length=150, verbose_name='Chuyên ngành')
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.degree} - {self.major} tại {self.university}"
