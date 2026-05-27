from django.db.models import Value
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector

from .models import Job, Application
from ..notifications.tasks import send_gotify_notification


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


@receiver(post_save, sender=Application)
def notify_employer_on_new_application(sender, instance, created, **kwargs):
    if not created:
        return

    employer_user_id = instance.job.company.employer_profile.pk
    job_title = instance.job.title

    candidate_name = instance.candidate_profile.user.get_full_name() or instance.candidate_profile.user.username

    title = "Có ứng viên mới!"
    message = f"Ứng viên {candidate_name} vừa nộp hồ sơ vào vị trí '{job_title}' của bạn."

    send_gotify_notification.delay(
        user_id=employer_user_id,
        title=title,
        message=message,
        priority=5
    )
