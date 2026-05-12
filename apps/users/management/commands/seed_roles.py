from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        roles = ['admin', 'employer', 'candidate']

        for role in roles:
            Group.objects.create(name=role)
