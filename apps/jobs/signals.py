from django.db.models import Value
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector

from .models import Job


@receiver(post_save, sender=Job)
def update_job_search_vector(sender, instance, **kwargs):
    company_name = instance.company.name if instance.company else ''
    Job.objects.filter(pk=instance.pk).update(
        search_vector=(
                SearchVector('title', weight='A', config='simple') +
                SearchVector(Value(company_name), weight='A', config='simple') +
                SearchVector('description', weight='B', config='simple') +
                SearchVector('requirements', weight='C', config='simple')
        )
    )
