import cloudinary.uploader
from django.core.management.base import BaseCommand

from apps.users.models import Country


class Command(BaseCommand):
    help = 'Seed default countries with flags to Cloudinary'

    def handle(self, *args, **kwargs):
        countries_data = [
            ("VN", "Vietnam"),
            ("US", "United States"),
            ("JP", "Japan"),
            ("KR", "South Korea"),
            ("FR", "France"),
            ("DE", "Germany"),
            ("CN", "China"),
            ("GB", "United Kingdom"),
        ]

        self.stdout.write("Bắt đầu khởi tạo dữ liệu quốc gia...")

        for code, name in countries_data:
            country, created = Country.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )

            if created or not country.image:
                flag_url = f"https://flagcdn.com/w320/{code.lower()}.png"

                try:
                    self.stdout.write(f"Đang upload cờ cho {name}...")

                    upload_result = cloudinary.uploader.upload(
                        flag_url,
                        folder="countries/flags/",
                        public_id=f"flag_{code.lower()}",
                        overwrite=True
                    )

                    country.image = upload_result['public_id']
                    country.save()

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Lỗi khi upload cờ {name}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("Hoàn thành seed dữ liệu quốc gia!"))
