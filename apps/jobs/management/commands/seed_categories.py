from django.core.management.base import BaseCommand
from django.db import transaction

from apps.jobs.models import Category


class Command(BaseCommand):
    help = 'Khởi tạo dữ liệu danh mục ngành nghề (IT, Luật, Tài chính/Ngân hàng/Bảo hiểm)'

    def handle(self, *args, **options):
        seed_data = {
            "Công nghệ thông tin": [
                "Software Development",
                "Infrastructure & Network",
                "Data & Analytics",
                "Information Security",
                "Software Testing (QA/QC)",
                "UI/UX Design",
                "IT Project Management",
                "AI & Machine Learning",
                "Cloud Computing",
                "IT Support / Helpdesk",
                "Blockchain Development",
                "Game Development"
            ],
            "Luật": [
                "Dịch vụ pháp lý (Agency/Firm)",
                "Dịch vụ pháp chế (In-house)"
            ],
            "Tài chính / Ngân hàng / Bảo hiểm": [
                "Tài chính",
                "Ngân hàng",
                "Chứng khoán",
                "Thẩm định và quản trị rủi ro",
                "Đầu tư và tài trợ",
                "Bảo hiểm"
            ]
        }

        self.stdout.write(self.style.HTTP_INFO("Bắt đầu khởi tạo dữ liệu danh mục..."))

        try:
            with transaction.atomic():
                total_parents = 0
                total_children = 0

                for parent_name, children_list in seed_data.items():
                    parent_obj, created_parent = Category.objects.get_or_create(
                        name=parent_name,
                        parent=None
                    )

                    if created_parent:
                        total_parents += 1
                        self.stdout.write(self.style.SUCCESS(f"\nĐã tạo Cha: [{parent_name}]"))
                    else:
                        self.stdout.write(self.style.WARNING(f"\nBỏ qua Cha: [{parent_name}] (Đã tồn tại)"))

                    for child_name in children_list:
                        child_obj, created_child = Category.objects.get_or_create(
                            name=child_name,
                            parent=parent_obj
                        )

                        if created_child:
                            total_children += 1
                            self.stdout.write(f"   + Thêm Con: {child_name}")

                self.stdout.write("\n" + "=" * 40)
                self.stdout.write(self.style.SUCCESS(
                    f"Hoàn tất! Đã tạo mới {total_parents} ngành Cha và {total_children} ngành Con."
                ))
                self.stdout.write("=" * 40 + "\n")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nCó lỗi xảy ra trong quá trình seed: {str(e)}"))
