import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from oauth2_provider.models import get_application_model

Application = get_application_model()
User = get_user_model()


class Command(BaseCommand):
    help = 'Tự động khởi tạo OAuth2 Application cho môi trường Development'

    def handle(self, *args, **options):
        client_id = settings.CLIENT_ID
        client_secret = settings.CLIENT_SECRET

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR('Thiếu CLIENT_ID hoặc CLIENT_SECRET trong .env'))
            return

        user = User.objects.filter(is_superuser=True).first()
        if not user:
            self.stdout.write(self.style.ERROR('Vui lòng tạo một superuser trước khi chạy lệnh này!'))
            return

        app, created = Application.objects.get_or_create(
            client_id=client_id,
            defaults={
                'user': user,
                'client_secret': client_secret,
                'client_type': Application.CLIENT_CONFIDENTIAL,
                'authorization_grant_type': Application.GRANT_PASSWORD,
                'name': 'Job Platform App',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Đã tạo thành công OAuth Application với ID: {client_id}'))
        else:
            self.stdout.write(self.style.WARNING('Application với Client ID này đã tồn tại sẵn trong DB.'))
