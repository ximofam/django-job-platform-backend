from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    User, CandidateProfile, EmployerProfile,
    Company, Experience, Education
)


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0
    fields = ('company', 'position', 'start_date', 'end_date', 'description')
    ordering = ('-start_date',)


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0
    fields = ('school', 'major', 'degree', 'start_date', 'end_date')
    ordering = ('-start_date',)


class CandidateProfileInline(admin.StackedInline):
    model = CandidateProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ ứng viên'
    fields = ('bio',)


class EmployerProfileInline(admin.StackedInline):
    model = EmployerProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ nhà tuyển dụng'
    fields = ('status', 'company', 'approved_by', 'approved_at')
    readonly_fields = ('approved_at',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'full_name', 'role',
        'gender', 'country', 'is_active', 'date_joined'
    )
    list_filter = ('role', 'gender', 'is_active', 'is_staff', 'country')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'avatar_preview')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Thông tin bổ sung', {
            'fields': (
                'role', 'gender', 'date_of_birth',
                'address', 'country', 'avatar', 'avatar_preview'
            )
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('email', 'role', 'gender', 'country')
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.is_candidate:
            return [CandidateProfileInline]
        if obj.is_employer:
            return [EmployerProfileInline]
        return []

    def full_name(self, obj):
        return obj.get_full_name() or '—'

    full_name.short_description = 'Họ tên'

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" height="80" style="border-radius:8px" />', obj.avatar.url)
        return '—'

    avatar_preview.short_description = 'Avatar'


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'created_at', 'updated_at')
    inlines = [ExperienceInline, EducationInline]

    def email(self, obj):
        return obj.user.email

    email.short_description = 'Email'


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'logo_preview', 'name', 'type', 'employee_size',
        'status', 'country', 'tax_code', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'type', 'employee_size', 'country')
    search_fields = ('name', 'tax_code', 'address')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('logo_preview', 'created_at', 'updated_at')
    list_editable = ('status',)

    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'logo', 'logo_preview', 'status')
        }),
        ('Chi tiết công ty', {
            'fields': ('type', 'employee_size', 'address', 'country', 'tax_code', 'description')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" height="36" style="border-radius:4px" />', obj.logo.url)
        return '—'

    logo_preview.short_description = 'Logo'


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'status', 'approved_by', 'approved_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email', 'company__name')
    readonly_fields = ('approved_at', 'created_at', 'updated_at')
    list_editable = ('status',)

    actions = ['approve_employers', 'deny_employers']

    @admin.action(description='Duyệt nhà tuyển dụng đã chọn')
    def approve_employers(self, request, queryset):
        pending_qs = queryset.filter(
            status__in=[EmployerProfile.Status.PENDING, EmployerProfile.Status.DENIED]
        ).select_related('user', 'company')

        if not pending_qs.exists():
            self.message_user(request, 'Không có nhà tuyển dụng nào đang chờ duyệt.', level='warning')
            return

        updated = 0
        errors = []

        for profile in pending_qs:
            try:
                with transaction.atomic():
                    profile.status = EmployerProfile.Status.APPROVED
                    profile.approved_by = request.user
                    profile.approved_at = timezone.now()
                    profile.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])

                    if profile.company:
                        profile.company.status = Company.Status.APPROVED
                        profile.company.save(update_fields=['status', 'updated_at'])

                    profile.user.assign_role(User.Role.EMPLOYER)
                    updated += 1
            except Exception as e:
                errors.append(f"{profile.user.username}: {str(e)}")

        if updated:
            self.message_user(request, f'{updated} nhà tuyển dụng đã được duyệt.')
        if errors:
            self.message_user(
                request,
                f'Lỗi khi duyệt: {", ".join(errors)}',
                level='error'
            )

    @admin.action(description='Từ chối nhà tuyển dụng đã chọn')
    def deny_employers(self, request, queryset):
        pending_qs = queryset.filter(
            status__in=[EmployerProfile.Status.PENDING, EmployerProfile.Status.APPROVED]
        ).select_related('user', 'company')

        if not pending_qs.exists():
            self.message_user(request, 'Không có nhà tuyển dụng nào đang chờ duyệt.', level='warning')
            return

        updated = 0
        for profile in pending_qs:
            profile.status = EmployerProfile.Status.DENIED
            profile.approved_by = request.user
            profile.approved_at = timezone.now()
            profile.save(update_fields=['status', 'approved_by', 'approved_at'])

            if profile.company:
                profile.company.status = Company.Status.DENIED
                profile.company.save(update_fields=['status'])

            profile.user.groups.clear()

            updated += 1

        self.message_user(request, f'{updated} nhà tuyển dụng đã bị từ chối.')
