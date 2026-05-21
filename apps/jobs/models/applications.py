from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import SoftDeleteModel, BaseModel


class Application(SoftDeleteModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Chờ xem xét")
        REVIEWING = "REVIEWING", _("Đang xem xét")
        INTERVIEW = "INTERVIEW", _("Phỏng vấn")
        ACCEPTED = "ACCEPTED", _("Chấp nhận")
        REJECTED = "REJECTED", _("Từ chối")
        WITHDRAWN = "WITHDRAWN", _("Ứng viên rút hồ sơ")

    candidate_profile = models.ForeignKey("users.CandidateProfile", on_delete=models.CASCADE,
                                          related_name="applications")
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expected_salary = models.PositiveIntegerField(null=True, blank=True)
    cv_file = models.ForeignKey("CandidateCV", on_delete=models.SET_NULL, null=True, related_name="applications")

    applied_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Ngày nộp"))
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Thời điểm NTD đầu tiên xem"))

    class Meta:
        verbose_name = _("Hồ sơ ứng tuyển")
        verbose_name_plural = _("Hồ sơ ứng tuyển")
        unique_together = [("candidate_profile", "job")]
        ordering = ["-applied_at"]

    @property
    def is_active(self):
        return self.status in (
            self.Status.PENDING,
            self.Status.REVIEWING,
            self.Status.INTERVIEW,
        )

    def withdraw(self):
        if self.status not in (self.Status.ACCEPTED, self.Status.REJECTED):
            self.status = self.Status.WITHDRAWN
            self.save(update_fields=["status", "updated_at"])


class CandidateCV(BaseModel):
    candidate_profile = models.ForeignKey("users.CandidateProfile", on_delete=models.CASCADE, related_name="cvs")
    title = models.CharField(max_length=200, verbose_name=_("Tên CV"))
    file = models.FileField(
        upload_to="candidates/cvs/%Y/%m/",
        verbose_name=_("File CV"),
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )]
    )

    class Meta:
        verbose_name = _("CV ứng viên")
        verbose_name_plural = _("CV ứng viên")
        ordering = ["-pk"]

    def __str__(self):
        return f"{self.candidate_profile} — {self.title}"
