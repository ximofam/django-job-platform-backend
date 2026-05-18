import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.locations.models import District, City

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_FILE = DATA_DIR / "locations.json"


class Command(BaseCommand):
    help = "Seed City and District data from a local JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            default=str(DEFAULT_FILE),
            help="Đường dẫn file JSON input (mặc định: apps/locations/data/locations.json)",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"])

        if not input_path.exists():
            raise CommandError(
                f"Không tìm thấy file: {input_path}\n"
                "Hãy chạy lệnh fetch_location_data trước để tải dữ liệu."
            )

        self.stdout.write(f"Đang đọc dữ liệu từ {input_path}...")
        with open(input_path, "r", encoding="utf-8") as f:
            provinces = json.load(f)

        total_cities = len(provinces)
        total_districts = sum(len(p["districts"]) for p in provinces)
        self.stdout.write(
            f"Tìm thấy {total_cities} tỉnh/thành, {total_districts} quận/huyện. Đang seed..."
        )

        with transaction.atomic():
            for p in provinces:
                city, _ = City.objects.update_or_create(
                    code=p["code"],
                    defaults={"name": p["name"]},
                )

                for d in p["districts"]:
                    District.objects.update_or_create(
                        city=city,
                        code=d["code"],
                        defaults={"name": d["name"]},
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Đã đồng bộ thành công {total_cities} tỉnh/thành và {total_districts} quận/huyện!"
        ))
