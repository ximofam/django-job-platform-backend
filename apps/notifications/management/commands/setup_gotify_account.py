import base64
import secrets
import requests
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.notifications.models import GotifyApplication

logger = logging.getLogger(__name__)
User = get_user_model()
admin_auth = (settings.GOTIFY_USER, settings.GOTIFY_PASSWORD)


class Command(BaseCommand):
    help = 'Tạo tài khoản và ứng dụng Gotify cho TẤT CẢ user hiện có chưa được setup.'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        total_users = users.count()

        self.stdout.write(self.style.NOTICE(f'Bắt đầu kiểm tra và setup Gotify cho {total_users} users...'))

        success_count = 0
        skip_count = 0
        error_count = 0

        for user in users:
            if GotifyApplication.objects.filter(user=user).exists():
                skip_count += 1
                self.stdout.write(f'[-] User {user.pk} đã có Gotify, bỏ qua.')
                continue

            try:
                self.setup_gotify_for_user(user)
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f'[+] Setup thành công cho user {user.pk}'))
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'[x] Lỗi khi setup user {user.pk}: {str(e)}'))

        self.stdout.write(self.style.NOTICE('=' * 40))
        self.stdout.write(self.style.SUCCESS(f'Hoàn thành!'))
        self.stdout.write(f'Thành công: {success_count}')
        self.stdout.write(f'Bỏ qua (Đã có sẵn): {skip_count}')
        self.stdout.write(f'Thất bại: {error_count}')

    def setup_gotify_for_user(self, user):
        gotify_user_pass = secrets.token_urlsafe(16)
        gotify_username = f"user_{user.pk}"

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
                user=user,
                app_id=app_data["id"],
                app_token=app_data["token"],
                basic_token=basic_token
            )

            logger.info(f"[Gotify] Successfully configured Gotify account, app, and client for user {user.pk}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"[Gotify] HTTP error for user {user.pk}: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"[Gotify] Unexpected error for user {user.pk}: {e}")
            raise e
