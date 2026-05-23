import uuid

from django.db import models

from common.models import SoftDeleteModel


class ServiceType(models.TextChoices):
    JOB_FEATURED = "JOB_FEATURED", "Tin tuyển dụng nổi bật"
    CANDIDATE_PRIORITY = "CANDIDATE_PRIORITY", "Hồ sơ ứng viên ưu tiên"


class PaymentMethod(models.TextChoices):
    PAYPAL = "PAYPAL", "PayPal"
    STRIPE = "STRIPE", "Stripe"
    MOMO = "MOMO", "MoMo"
    ZALOPAY = "ZALOPAY", "ZaloPay"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Chờ xử lý"
    COMPLETED = "COMPLETED", "Thành công"
    FAILED = "FAILED", "Thất bại"
    REFUNDED = "REFUNDED", "Đã hoàn tiền"


class Payment(SoftDeleteModel):
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="payments")
    service_type = models.CharField(max_length=30, choices=ServiceType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    gateway_ref = models.CharField(max_length=255, blank=True, help_text="Mã giao dịch từ cổng")
    gateway_response = models.JSONField(default=dict, blank=True)
    meta_data = models.JSONField(default=dict, blank=True)
    currency = models.CharField(max_length=3, default="VND")

    class Meta:
        ordering = ["-pk"]
