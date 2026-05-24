import requests
import logging
import json

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import GotifyApplication

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_gotify_notification(user_id: int, title: str, message: any, priority: int = 5) -> bool:
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error(f"[Gotify] Không tìm thấy User với ID {user_id}")
        return False

    g_app = GotifyApplication.objects.filter(user=user).first()

    if not g_app:
        logger.warning(f"[Gotify] User {user_id} chưa có cấu hình tài khoản Gotify.")
        return False

    if not g_app.app_token:
        logger.error(f"[Gotify] User {user_id} thiếu app_token trong Database.")
        return False

    if isinstance(message, (dict, list)):
        final_message = json.dumps(message, ensure_ascii=False)
    else:
        final_message = str(message)

    try:
        response = requests.post(
            f"{settings.GOTIFY_URL}/message",
            headers={"X-Gotify-Key": g_app.app_token},
            json={
                "title": title,
                "message": final_message,
                "priority": priority
            },
            timeout=5
        )
        response.raise_for_status()

        logger.info(f"[Gotify] Đã gửi thông báo thành công tới user {user_id}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"[Gotify] Gọi API thất bại cho user {user_id}. Chi tiết: {e}")
        return False
    except Exception as e:
        logger.error(f"[Gotify] Lỗi hệ thống không xác định khi gửi thông báo: {e}")
        return False
