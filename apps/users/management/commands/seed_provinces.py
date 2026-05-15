import requests
from django.core.management.base import BaseCommand
from apps.users.models import Province


class Command(BaseCommand):
    help = 'Tự động tải và seed dữ liệu 63 tỉnh thành Việt Nam vào Database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Đang tải dữ liệu từ API...'))

        url = "https://provinces.open-api.vn/api/p/"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            count = 0
            for item in data:
                province, created = Province.objects.get_or_create(
                    code=str(item['code']),
                    defaults={
                        'name': item['name'],
                        'codename': item['codename']
                    }
                )
                if created:
                    count += 1

            self.stdout.write(self.style.SUCCESS(f'Thành công! Đã thêm mới {count} tỉnh thành vào Database.'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Lỗi khi gọi API: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Đã xảy ra lỗi: {e}'))
