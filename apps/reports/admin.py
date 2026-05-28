from django.contrib import admin
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from datetime import timedelta
import json

from apps.jobs.models import Job, Application, CandidateCV


class JobAdminSite(admin.AdminSite):
    site_header = "Quản trị Tuyển dụng"
    site_title = "Tuyển dụng Admin"
    index_title = "Bảng điều khiển"


class StatisticsMixin:
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "statistics/",
                self.admin_site.admin_view(self.statistics_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_statistics",
            ),
        ]
        return custom + urls

    def statistics_view(self, request):
        raise NotImplementedError("Subclass phải implement statistics_view()")


def _date_range_filter(days: int):
    since = timezone.now() - timedelta(days=days)
    return {"created_at__gte": since}


def _job_stats(days: int | None = None):
    qs = Job.objects.all()
    if days:
        qs = qs.filter(**_date_range_filter(days))

    total = qs.count()
    by_status = dict(
        qs.values("status").annotate(n=Count("id")).values_list("status", "n")
    )
    by_employment_type = dict(
        qs.values("employment_type").annotate(n=Count("id")).values_list("employment_type", "n")
    )
    by_experience = dict(
        qs.values("experience_level").annotate(n=Count("id")).values_list("experience_level", "n")
    )

    monthly = list(
        Job.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=365)
        )
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(n=Count("id"))
        .order_by("month")
        .values_list("month", "n")
    )

    return {
        "total": total,
        "published": by_status.get("PUBLISHED", 0),
        "draft": by_status.get("DRAFT", 0),
        "expired": by_status.get("EXPIRED", 0),
        "closed": by_status.get("CLOSED", 0),
        "by_employment_type": by_employment_type,
        "by_experience": by_experience,
        "monthly": [(m.strftime("%m/%Y") if m else "", n) for m, n in monthly],
    }


def _application_stats(days: int | None = None):
    qs = Application.objects.all()
    if days:
        qs = qs.filter(applied_at__gte=timezone.now() - timedelta(days=days))

    total = qs.count()
    by_status = dict(
        qs.values("status").annotate(n=Count("id")).values_list("status", "n")
    )

    unique_candidates = qs.values("candidate_profile").distinct().count()

    top_jobs = list(
        qs.values("job__title", "job__id")
        .annotate(n=Count("id"))
        .order_by("-n")[:10]
        .values_list("job__title", "n")
    )

    monthly = list(
        Application.objects.filter(
            applied_at__gte=timezone.now() - timedelta(days=365)
        )
        .annotate(month=TruncMonth("applied_at"))
        .values("month")
        .annotate(n=Count("id"))
        .order_by("month")
        .values_list("month", "n")
    )

    daily = list(
        Application.objects.filter(
            applied_at__gte=timezone.now() - timedelta(days=30)
        )
        .annotate(day=TruncDate("applied_at"))
        .values("day")
        .annotate(n=Count("id"))
        .order_by("day")
        .values_list("day", "n")
    )

    return {
        "total": total,
        "unique_candidates": unique_candidates,
        "pending": by_status.get("PENDING", 0),
        "reviewing": by_status.get("REVIEWING", 0),
        "interview": by_status.get("INTERVIEW", 0),
        "accepted": by_status.get("ACCEPTED", 0),
        "rejected": by_status.get("REJECTED", 0),
        "withdrawn": by_status.get("WITHDRAWN", 0),
        "top_jobs": top_jobs,
        "monthly": [(m.strftime("%m/%Y") if m else "", n) for m, n in monthly],
        "daily": [(d.strftime("%d/%m") if d else "", n) for d, n in daily],
    }


@admin.register(Job)
class JobAdmin(StatisticsMixin, admin.ModelAdmin):
    list_display = (
        "title", "company", "status_badge", "employment_type",
        "experience_level", "applications_count", "published_at", "expired_at",
    )
    list_filter = ("status", "employment_type", "experience_level", "category")
    search_fields = ("title", "company__name")
    readonly_fields = ("published_at",)
    date_hierarchy = "created_at"

    change_list_template = "admin/jobs/job/change_list.html"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _applications_count=Count("applications")
        )

    @admin.display(description="Số đơn", ordering="_applications_count")
    def applications_count(self, obj):
        return obj._applications_count

    @admin.display(description="Trạng thái")
    def status_badge(self, obj):
        colors = {
            "PUBLISHED": "#16a34a",
            "DRAFT": "#ca8a04",
            "EXPIRED": "#dc2626",
            "CLOSED": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        label = obj.get_status_display()
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color, label,
        )

    def statistics_view(self, request):
        days = int(request.GET.get("days", 30))
        job_stats = _job_stats(days)
        app_stats = _application_stats(days)

        job_monthly_labels = [m for m, _ in job_stats["monthly"]]
        job_monthly_data = [n for _, n in job_stats["monthly"]]
        app_monthly_labels = [m for m, _ in app_stats["monthly"]]
        app_monthly_data = [n for _, n in app_stats["monthly"]]
        app_daily_labels = [d for d, _ in app_stats["daily"]]
        app_daily_data = [n for _, n in app_stats["daily"]]

        context = {
            **self.admin_site.each_context(request),
            "title": "Thống kê tuyển dụng",
            "days": days,
            "job_stats": job_stats,
            "app_stats": app_stats,

            "job_monthly_labels": json.dumps(job_monthly_labels),
            "job_monthly_data": json.dumps(job_monthly_data),
            "app_monthly_labels": json.dumps(app_monthly_labels),
            "app_monthly_data": json.dumps(app_monthly_data),
            "app_daily_labels": json.dumps(app_daily_labels),
            "app_daily_data": json.dumps(app_daily_data),

            "job_status_labels": json.dumps([
                "Đang hiển thị", "Bản nháp", "Hết hạn", "Đã đóng"
            ]),
            "job_status_data": json.dumps([
                job_stats["published"], job_stats["draft"],
                job_stats["expired"], job_stats["closed"],
            ]),

            "app_status_labels": json.dumps([
                "Chờ xem xét", "Đang xem xét", "Phỏng vấn",
                "Chấp nhận", "Từ chối", "Rút hồ sơ",
            ]),
            "app_status_data": json.dumps([
                app_stats["pending"], app_stats["reviewing"],
                app_stats["interview"], app_stats["accepted"],
                app_stats["rejected"], app_stats["withdrawn"],
            ]),
        }
        return TemplateResponse(
            request, "admin/jobs/job/statistics.html", context
        )


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "candidate_profile", "job", "status_badge",
        "applied_at", "viewed_at",
    )
    list_filter = ("status",)
    search_fields = ("candidate_profile__user__email", "job__title")
    readonly_fields = ("applied_at", "viewed_at")
    date_hierarchy = "applied_at"

    @admin.display(description="Trạng thái")
    def status_badge(self, obj):
        colors = {
            "PENDING": "#ca8a04",
            "REVIEWING": "#2563eb",
            "INTERVIEW": "#7c3aed",
            "ACCEPTED": "#16a34a",
            "REJECTED": "#dc2626",
            "WITHDRAWN": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color, obj.get_status_display(),
        )


@admin.register(CandidateCV)
class CandidateCVAdmin(admin.ModelAdmin):
    list_display = ("candidate_profile", "title", "created_at")
    search_fields = ("candidate_profile__user__email", "title")
