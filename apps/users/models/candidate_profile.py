from apps.users.models import User
from common.models import BaseModel
from django.db import models


class CandidateProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile", primary_key=True)
    bio = models.TextField(null=True, blank=True)


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
