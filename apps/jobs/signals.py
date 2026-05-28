from django.conf import settings
from django.db.models import Value, Func, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector

from .models import Job, Application
from .tasks import expire_single_job
from .utils import remove_vietnamese_accents
from ..notifications.tasks import send_gotify_notification


@receiver(post_save, sender=Job)
def update_job_search_vector(sender, instance, **kwargs):
    company_name = instance.company.name if instance.company else ''

    Job.objects.filter(pk=instance.pk).update(
        search_vector=(SearchVector(Value(remove_vietnamese_accents(instance.title)),
                                    weight='A', config='simple') +
                       SearchVector(Value(remove_vietnamese_accents(company_name)),
                                    weight='A', config='simple') +
                       SearchVector(Value(remove_vietnamese_accents(instance.description)),
                                    weight='B', config='simple') +
                       SearchVector(Value(remove_vietnamese_accents(instance.requirements or '')),
                                    weight='C', config='simple')
                       )
    )


@receiver(post_save, sender=Job)
def schedule_job_expiry(sender, instance, created, **kwargs):
    if created:
        expire_single_job.apply_async(
            args=[instance.pk],
            countdown=settings.JOB_DRAFT_EXPIRE_SECONDS,
            task_id=f"expire-job-{instance.pk}"
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
