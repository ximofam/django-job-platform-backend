from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Company
from .tasks import update_company_jobs_search_vectors


@receiver(pre_save, sender=Company)
def track_company_name_change(sender, instance, **kwargs):
    if not instance.pk:
        instance._name_changed = False
        return

    try:
        old = Company.objects.get(pk=instance.pk)
        instance._name_changed = old.name != instance.name
    except Company.DoesNotExist:
        instance._name_changed = False


@receiver(post_save, sender=Company)
def reindex_company_jobs(sender, instance, **kwargs):
    if getattr(instance, '_name_changed', False):
        update_company_jobs_search_vectors.delay(instance.pk)
