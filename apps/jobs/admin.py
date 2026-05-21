from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import Job, Category


class JobStatisticsView(UserPassesTestMixin, TemplateView):
    template_name = "admin/job_statistics.html"

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # --- 1. THỐNG KÊ TỔNG QUAN ---
        context['total_jobs'] = Job.objects.count()
        context['published_jobs'] = Job.objects.filter(status=Job.Status.PUBLISHED).count()
        context['new_jobs_30d'] = Job.objects.filter(created_at__gte=thirty_days_ago).count()  # Hoặc dùng published_at

        # Lấy từ điển nhãn tiếng Việt từ TextChoices
        type_dict = dict(Job.EmploymentType.choices)
        level_dict = dict(Job.ExperienceLevel.choices)
        status_dict = dict(Job.Status.choices)

        # --- 2. THỐNG KÊ THEO LOẠI HÌNH (Employment Type) ---
        type_qs = Job.objects.values('employment_type').annotate(total=Count('id')).order_by('-total')
        context['jobs_by_type'] = [
            {'label': type_dict.get(item['employment_type'], 'Khác'), 'total': item['total']}
            for item in type_qs
        ]

        # --- 3. THỐNG KÊ THEO CẤP ĐỘ KINH NGHIỆM (Experience Level) ---
        level_qs = Job.objects.values('experience_level').annotate(total=Count('id')).order_by('-total')
        context['jobs_by_level'] = [
            {'label': level_dict.get(item['experience_level'], 'Chưa cập nhật'), 'total': item['total']}
            for item in level_qs if item['experience_level']  # Bỏ qua null
        ]

        # --- 4. THỐNG KÊ THEO TRẠNG THÁI (Status) ---
        status_qs = Job.objects.values('status').annotate(total=Count('id')).order_by('-total')
        context['jobs_by_status'] = [
            {'label': status_dict.get(item['status'], 'Khác'), 'total': item['total']}
            for item in status_qs
        ]

        # --- 5. TOP DANH MỤC CÓ NHIỀU JOB NHẤT ---
        # Chỉ lấy 5 danh mục đứng đầu
        context['top_categories'] = Category.objects.annotate(
            job_count=Count('jobs')
        ).filter(job_count__gt=0).order_by('-job_count')[:5]

        # --- CẤU HÌNH GIAO DIỆN UNFOLD ---
        context['title'] = "Thống kê Việc làm"
        context['site_header'] = "Quản trị Job Platform"

        return context
