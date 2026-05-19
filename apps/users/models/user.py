from django.contrib.auth.models import AbstractUser, Group
from django.db import models, transaction

from apps.locations.models import Country


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
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, related_name='users')

    @property
    def profile(self):
        if hasattr(self, 'candidate_profile'):
            return self.candidate_profile
        elif hasattr(self, 'employer_profile'):
            return self.employer_profile
        return None

    @transaction.atomic
    def assign_role(self, role):
        valid_roles = [r[0] for r in User.Role.choices]
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
