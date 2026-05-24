import base64
import secrets
import requests
import logging
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import GotifyApplication

logger = logging.getLogger(__name__)
User = get_user_model()
admin_auth = (settings.GOTIFY_USER, settings.GOTIFY_PASSWORD)


@receiver(post_save, sender=User)
def setup_gotify_for_new_user(sender, instance, created, **kwargs):
    if not created:
        return

    gotify_user_pass = secrets.token_urlsafe(16)
    gotify_username = f"user_{instance.pk}"

    credentials = f"{gotify_username}:{gotify_user_pass}"
    basic_token = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    try:
        user_res = requests.post(
            f"{settings.GOTIFY_URL}/user",
            auth=admin_auth,
            json={
                "name": gotify_username,
                "pass": gotify_user_pass,
                "admin": False
            },
            timeout=5
        )
        user_res.raise_for_status()

        user_auth = (gotify_username, gotify_user_pass)
        app_res = requests.post(
            f"{settings.GOTIFY_URL}/application",
            auth=user_auth,
            json={
                "name": "Job platform notifications",
                "description": "Thông báo từ hệ thống"
            },
            timeout=5
        )
        app_res.raise_for_status()
        app_data = app_res.json()

        GotifyApplication.objects.create(
            user=instance,
            app_id=app_data["id"],
            app_token=app_data["token"],
            basic_token=basic_token
        )

        logger.info(f"[Gotify] Successfully configured Gotify account, app, and client for user {instance.pk}")

    except requests.exceptions.HTTPError as e:
        logger.error(f"[Gotify] HTTP error for user {instance.pk}: {e.response.text}")
    except Exception as e:
        logger.error(f"[Gotify] Unexpected error for user {instance.pk}: {e}")
