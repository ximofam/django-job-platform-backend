from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.jobs.models import Job
import logging

from apps.notifications.tasks import send_gotify_notification
from apps.users.models import EmployerProfile

logger = logging.getLogger(__name__)


@shared_task
def expire_single_job(job_id: int):
    try:
        job = Job.objects.get(id=job_id)

        if job.status == Job.Status.DRAFT:
            job.delete()
            logger.info(f"Job {job_id} là DRAFT -> đã xóa.")

            employer = EmployerProfile.objects.filter(company_id=job.company_id).first()
            if employer:
                title = "Đã xóa bản nháp của job"
                message = f"Công việc {job.title} đã bị xóa."
                send_gotify_notification.delay(employer.pk, title, message)

        elif job.status == Job.Status.PUBLISHED:
            delay = (job.expired_at - timezone.now()).total_seconds()

            if delay > 0:
                _do_expire_job.apply_async(
                    args=[job_id],
                    countdown=delay,
                    task_id=f"do-expire-job-{job_id}"
                )
                logger.info(f"Job {job_id} -> đã lên lịch expire sau {delay:.0f}s.")
            else:
                _do_expire_job.delay(job_id)
                logger.info(f"Job {job_id} -> đã quá hạn, expire ngay.")

        else:
            logger.info(f"Job {job_id} có status '{job.status}' -> bỏ qua.")

    except Job.DoesNotExist:
        logger.warning(f"Job {job_id} không tồn tại.")


@shared_task
def _do_expire_job(job_id: int):
    try:
        job = Job.objects.get(id=job_id, status=Job.Status.PUBLISHED)
        job.status = Job.Status.EXPIRED
        job.save(update_fields=['status'])

        employer = EmployerProfile.objects.filter(company_id=job.company_id).first()
        if employer:
            title = "Có công việc đã hết hạn!!!!"
            message = f"Công việc {job.title} đã hêt hạn."
            send_gotify_notification.delay(employer.pk, title, message)

        logger.info(f"Job {job_id} đã được expire.")

    except Job.DoesNotExist:
        logger.warning(f"Job {job_id} không còn ở trạng thái PUBLISHED.")


@shared_task(bind=True, max_retries=3)
def expire_jobs(self):
    try:
        now = timezone.now()

        with transaction.atomic():
            expired_jobs = Job.objects.filter(
                status=Job.Status.PUBLISHED,
                expired_at__lt=now,
            ).select_related('company')

            job_ids = list(expired_jobs.values_list('id', flat=True))

            expired_jobs.update(status=Job.Status.EXPIRED)

        for job_id in job_ids:
            notify_expired_job.delay(job_id)

        logger.info(f"[expire_jobs] Expired {len(job_ids)} jobs at {now}")
        return {"expired_count": len(job_ids)}

    except Exception as exc:
        logger.error(f"[expire_jobs] Failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def notify_expired_job(self, job_id):
    try:
        job = Job.objects.get(id=job_id)

        employer = EmployerProfile.objects.filter(company_id=job.company_id).first()
        if employer:
            title = "Có công việc đã hết hạn!!!!"
            message = f"Công việc {job.title} đã hết hạn."
            send_gotify_notification.delay(employer.pk, title, message)
            logger.info(f"[notify_expired_job] Sent notification for job {job_id}")

    except Job.DoesNotExist:
        logger.warning(f"[notify_expired_job] Job {job_id} not found")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
