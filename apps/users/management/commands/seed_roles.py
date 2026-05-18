from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.jobs.models import Job
from apps.users.models import User


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        roles = [r[0] for r in User.Role.choices]

        for role in roles:
            Group.objects.get_or_create(name=role)

        employer_group = Group.objects.get(name=User.Role.EMPLOYER)

        content_type = ContentType.objects.get_for_model(Job)

        permissions = Permission.objects.filter(
            content_type=content_type
        )

        employer_group.permissions.add(*permissions)

        self.stdout.write(
            self.style.SUCCESS(
                "Added Job permissions to EMPLOYER group"
            )
        )
