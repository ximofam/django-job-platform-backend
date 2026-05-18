from celery import shared_task
from django.contrib.postgres.search import SearchVector
from django.db.models import Value
from django.db.models.functions import Coalesce

from apps.jobs.models import Job
from .models import Company


@shared_task
def update_company_jobs_search_vectors(company_id):
    company = Company.objects.get(pk=company_id)

    Job.objects.filter(company_id=company_id).update(
        search_vector=(
                SearchVector(Value(company.name or ""), weight="A", config="simple") +
                SearchVector("title", weight="A", config="simple") +
                SearchVector(Coalesce("description", Value("")), weight="B", config="simple") +
                SearchVector(Coalesce("requirements", Value("")), weight="C", config="simple")
        )
    )
