import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.locations.models import District, City


class Command(BaseCommand):
    help = "Seed City and District data from provinces.open-api.vn"

    def handle(self, *args, **options):
        self.stdout.write("Đang tải danh sách tỉnh/thành phố...")

        session = requests.Session()

        res_provinces = session.get("https://provinces.open-api.vn/api/v2/p/", timeout=15)
        res_provinces.raise_for_status()
        provinces = res_provinces.json()

        self.stdout.write("Đang tải chi tiết quận/huyện và lưu database...")

        with transaction.atomic():
            for idx, p in enumerate(provinces, 1):
                city, _ = City.objects.update_or_create(
                    code=p['code'],
                    defaults={"name": p['name']},
                )

                detail_url = f"https://provinces.open-api.vn/api/v2/p/{p['code']}?depth=2"
                res_detail = session.get(detail_url, timeout=15)

                if res_detail.status_code == 200:
                    districts = res_detail.json().get("wards", [])

                    for d in districts:
                        District.objects.update_or_create(
                            city=city,
                            code=d['code'],
                            defaults={"name": d["name"]},
                        )

        self.stdout.write(self.style.SUCCESS("Đã đồng bộ dữ liệu thành công!"))
