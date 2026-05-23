from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from apps.users.models import Company
from common.models import BaseModel, SoftDeleteModel
from django.core.exceptions import ValidationError


class Category(BaseModel):
    name = models.CharField(max_length=50, null=False, blank=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        ordering = ['name']

    def clean(self):
        super().clean()

        if self.parent:
            if self.parent.parent is not None:
                raise ValidationError({
                    'parent': 'Hệ thống chỉ cho phép tối đa 2 cấp (Cha -> Con). Danh mục bạn chọn làm cha hiện tại đang là một danh mục con.'
                })

            if self.pk and self.children.exists():
                raise ValidationError({
                    'parent': 'Danh mục này đang có danh mục con bên trong, do đó không thể gán nó làm con của một danh mục khác.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Job(SoftDeleteModel):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Toàn thời gian'
        PART_TIME = 'PART_TIME', 'Bán thời gian'
        CONTRACT = 'CONTRACT', 'Hợp đồng'
        FREELANCE = 'FREELANCE', 'Tự do'
        INTERNSHIP = 'INTERNSHIP', 'Thực tập'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Bản nháp'
        PUBLISHED = 'PUBLISHED', 'Đang hiển thị'
        EXPIRED = 'EXPIRED', 'Đã hết hạn'
        CLOSED = 'CLOSED', 'Đã đóng'

    class ExperienceLevel(models.TextChoices):
        INTERN = 'INTERN', 'Thực tập sinh'
        FRESHER = 'FRESHER', 'Fresher'
        JUNIOR = 'JUNIOR', 'Junior'
        MIDDLE = 'MIDDLE', 'Middle'
        SENIOR = 'SENIOR', 'Senior'
        LEAD = 'LEAD', 'Lead / Manager'

    search_vector = SearchVectorField(null=True, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')

    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.INTERNSHIP)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, null=True)

    title = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    requirements = models.TextField(null=False, blank=False)
    benefit = models.TextField(null=False, blank=False)
    address = models.ForeignKey('locations.Address', on_delete=models.PROTECT, related_name='jobs')

    salary_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='VND')

    boost_score = models.IntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
            GinIndex(fields=['title'], name='job_title_trgm_idx', opclasses=['gin_trgm_ops']),
        ]

# class JobView(BaseModel):
#     job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='views')
#
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     session_key = models.CharField(max_length=40, null=True, blank=True)
#     ip_address = models.GenericIPAddressField(null=True, blank=True)
#     user_agent = models.CharField(max_length=255, null=True, blank=True)
#
#     view_count = models.PositiveIntegerField(default=0)
#     duration_seconds = models.PositiveIntegerField(default=0)
