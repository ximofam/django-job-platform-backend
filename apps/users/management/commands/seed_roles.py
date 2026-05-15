from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.users.models import User


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        roles = [r[0] for r in User.Role.choices]

        for role in roles:
            Group.objects.create(name=role)
