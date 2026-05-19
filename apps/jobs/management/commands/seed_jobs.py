from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.jobs.models import Job, Category
from apps.users.models import Company

JOBS_DATA = {
    "0101248141": [  # FPT Software
        {
            "title": "Senior Java Backend Developer",
            "category_name": "Software Development",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.SENIOR,
            "status": Job.Status.PUBLISHED,
            "address": "Tòa nhà FPT, Phố Duy Tân, Cầu Giấy, Hà Nội",
            "salary_min": 40_000_000,
            "salary_max": 70_000_000,
            "salary_currency": "VND",
            "expired_at_days": 30,
            "description": """FPT Software tìm kiếm Senior Java Developer có kinh nghiệm xây dựng hệ thống backend hiệu suất cao cho các dự án outsourcing quốc tế.

Bạn sẽ tham gia vào đội ngũ phát triển phần mềm cho khách hàng tại Nhật Bản, Hàn Quốc và châu Âu, làm việc với các công nghệ hiện đại trong môi trường Agile/Scrum chuyên nghiệp.""",
            "requirements": """- Tối thiểu 4 năm kinh nghiệm với Java (Spring Boot, Spring MVC, Spring Data)
- Thành thạo thiết kế RESTful API và microservices architecture
- Kinh nghiệm với PostgreSQL / MySQL và tối ưu hóa query
- Hiểu biết về Docker, Kubernetes là lợi thế
- Khả năng đọc hiểu tài liệu và giao tiếp bằng tiếng Anh (B2 trở lên)
- Có kinh nghiệm làm việc với mô hình Agile/Scrum""",
            "benefit": """- Lương cạnh tranh, review 2 lần/năm
- Thưởng dự án, thưởng hiệu suất cuối năm
- 15 ngày phép/năm + các ngày lễ theo quy định
- Bảo hiểm sức khỏe cao cấp cho nhân viên và người thân
- Cơ hội công tác nước ngoài (Nhật, Hàn, EU)
- Lộ trình thăng tiến rõ ràng: Senior → Tech Lead → Architect""",
        },
        {
            "title": "DevOps / Cloud Engineer",
            "category_name": "Cloud Computing",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.MIDDLE,
            "status": Job.Status.PUBLISHED,
            "address": "Tòa nhà FPT Tân Thuận, Quận 7, TP. Hồ Chí Minh",
            "salary_min": 30_000_000,
            "salary_max": 55_000_000,
            "salary_currency": "VND",
            "expired_at_days": 45,
            "description": """Chúng tôi đang tìm kiếm DevOps Engineer để xây dựng và vận hành hạ tầng cloud cho các hệ thống phần mềm quy mô lớn phục vụ khách hàng toàn cầu của FPT Software.""",
            "requirements": """- 2–4 năm kinh nghiệm DevOps/Cloud
- Thành thạo ít nhất một nền tảng cloud: AWS, GCP hoặc Azure
- Kinh nghiệm CI/CD: Jenkins, GitLab CI, GitHub Actions
- Sử dụng thành thạo Docker và Kubernetes
- Kinh nghiệm với Infrastructure as Code (Terraform, Ansible)
- Hiểu biết về monitoring: Prometheus, Grafana, ELK Stack""",
            "benefit": """- Lương thỏa thuận theo năng lực
- Hỗ trợ thi chứng chỉ cloud (AWS/GCP/Azure) 100%
- Làm việc với hệ thống quy mô lớn, môi trường quốc tế
- Chế độ WFH linh hoạt 2 ngày/tuần
- 14 ngày phép năm + nghỉ lễ đầy đủ""",
        },
        {
            "title": "Thực tập sinh Kiểm thử Phần mềm (QA Intern)",
            "category_name": "Software Testing (QA/QC)",
            "employment_type": Job.EmploymentType.INTERNSHIP,
            "experience_level": Job.ExperienceLevel.INTERN,
            "status": Job.Status.PUBLISHED,
            "address": "Tòa nhà FPT, Phố Duy Tân, Cầu Giấy, Hà Nội",
            "salary_min": 3_000_000,
            "salary_max": 5_000_000,
            "salary_currency": "VND",
            "expired_at_days": 20,
            "description": """FPT Software mở chương trình thực tập dành cho sinh viên ngành CNTT muốn tìm hiểu về quy trình kiểm thử phần mềm trong môi trường doanh nghiệp lớn.""",
            "requirements": """- Sinh viên năm 3, năm 4 ngành CNTT hoặc liên quan
- Có kiến thức cơ bản về SDLC và vòng đời kiểm thử
- Ham học hỏi, chịu khó, có tinh thần trách nhiệm
- Ưu tiên ứng viên đã biết Selenium, Postman hoặc JMeter""",
            "benefit": """- Trợ cấp thực tập hấp dẫn
- Được mentor 1-1 bởi QA senior có kinh nghiệm
- Cấp laptop trong thời gian thực tập
- Cơ hội được nhận vào làm chính thức sau thực tập
- Cấp chứng nhận thực tập có giá trị""",
        },
    ],
    "0303456789": [  # VNG Corporation
        {
            "title": "Senior Backend Engineer (Golang)",
            "category_name": "Software Development",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.SENIOR,
            "status": Job.Status.PUBLISHED,
            "address": "VNG Campus, 182 Lê Đại Hành, Quận 11, TP. Hồ Chí Minh",
            "salary_min": 50_000_000,
            "salary_max": 90_000_000,
            "salary_currency": "VND",
            "expired_at_days": 30,
            "description": """VNG tìm kiếm Backend Engineer (Golang) để phát triển các dịch vụ core cho nền tảng Zalo — ứng dụng nhắn tin với hơn 75 triệu người dùng tại Việt Nam.

Bạn sẽ làm việc trong team hệ thống phân tán, xử lý hàng tỷ message mỗi ngày, với yêu cầu cao về hiệu suất, độ ổn định và khả năng mở rộng.""",
            "requirements": """- 4+ năm kinh nghiệm backend, tối thiểu 2 năm với Golang
- Hiểu sâu về distributed systems, message queue (Kafka, RabbitMQ)
- Kinh nghiệm xây dựng và vận hành microservices ở quy mô lớn
- Thành thạo Redis, MySQL/PostgreSQL
- Hiểu biết về low-latency system design
- Có kinh nghiệm với gRPC là điểm cộng""",
            "benefit": """- Mức lương top thị trường, review hàng năm
- Cổ phần ESOP cho nhân sự cấp cao
- Campus VNG đẳng cấp: gym, bể bơi, sân thể thao
- Bữa trưa miễn phí tại canteen
- Bảo hiểm sức khỏe VIP cho cả gia đình
- Budget học tập và tham dự hội nghị quốc tế""",
        },
        {
            "title": "AI/ML Engineer – Recommendation System",
            "category_name": "AI & Machine Learning",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.MIDDLE,
            "status": Job.Status.PUBLISHED,
            "address": "VNG Campus, 182 Lê Đại Hành, Quận 11, TP. Hồ Chí Minh",
            "salary_min": 40_000_000,
            "salary_max": 75_000_000,
            "salary_currency": "VND",
            "expired_at_days": 40,
            "description": """Nhóm AI của VNG đang phát triển hệ thống recommendation và ranking cho các sản phẩm nội dung (ZingMP3, ZingTV). Bạn sẽ nghiên cứu và triển khai các thuật toán gợi ý cá nhân hóa phục vụ hàng chục triệu người dùng.""",
            "requirements": """- 2–5 năm kinh nghiệm Machine Learning / Deep Learning
- Thành thạo Python, PyTorch hoặc TensorFlow
- Kinh nghiệm với collaborative filtering, content-based filtering, hoặc two-tower model
- Hiểu biết về xây dựng feature pipeline và MLOps
- Có kinh nghiệm triển khai model lên production
- Nền tảng toán học vững: xác suất, đại số tuyến tính, tối ưu hóa""",
            "benefit": """- Làm việc với data thực tế quy mô hàng chục triệu user
- Môi trường nghiên cứu cởi mở, khuyến khích publish paper
- Budget GPU/cloud không giới hạn cho experiment
- Tham gia các hội nghị AI quốc tế (NeurIPS, ICML)
- Lương cạnh tranh + thưởng hiệu suất""",
        },
    ],
    "0312345678": [  # Tiki
        {
            "title": "Frontend Engineer (React/TypeScript)",
            "category_name": "Software Development",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.JUNIOR,
            "status": Job.Status.PUBLISHED,
            "address": "Tầng 6, 52 Út Tịch, Phường 4, Quận Tân Bình, TP. Hồ Chí Minh",
            "salary_min": 18_000_000,
            "salary_max": 30_000_000,
            "salary_currency": "VND",
            "expired_at_days": 25,
            "description": """Tiki đang tìm kiếm Frontend Engineer gia nhập đội ngũ phát triển giao diện cho nền tảng thương mại điện tử hàng đầu Việt Nam với hàng triệu lượt truy cập mỗi ngày.""",
            "requirements": """- 1–3 năm kinh nghiệm Frontend
- Thành thạo React.js và TypeScript
- Có kiến thức tốt về HTML5, CSS3, responsive design
- Hiểu biết về state management (Redux, Zustand hoặc React Query)
- Quen thuộc với Git workflow và code review
- Có kinh nghiệm tối ưu hóa Web Performance là lợi thế""",
            "benefit": """- Lương hấp dẫn + thưởng theo quý
- Làm việc với traffic thực tế hàng triệu user
- Văn phòng trung tâm, cơ sở vật chất hiện đại
- Bảo hiểm sức khỏe, nghỉ phép 14 ngày/năm
- Chương trình đào tạo và phát triển kỹ năng""",
        },
        {
            "title": "Data Analyst – E-commerce Insights",
            "category_name": "Data & Analytics",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.MIDDLE,
            "status": Job.Status.PUBLISHED,
            "address": "Tầng 6, 52 Út Tịch, Phường 4, Quận Tân Bình, TP. Hồ Chí Minh",
            "salary_min": 22_000_000,
            "salary_max": 38_000_000,
            "salary_currency": "VND",
            "expired_at_days": 35,
            "description": """Tiki cần Data Analyst phân tích hành vi mua sắm, đo lường hiệu quả chiến dịch và cung cấp insight cho các đội product, marketing và kinh doanh.""",
            "requirements": """- 2–4 năm kinh nghiệm Data Analytics
- Thành thạo SQL (BigQuery, PostgreSQL)
- Sử dụng tốt Python (pandas, numpy) hoặc R cho phân tích
- Kinh nghiệm trực quan hóa dữ liệu: Tableau, Metabase hoặc Looker
- Tư duy phân tích sắc bén, khả năng kể chuyện bằng dữ liệu
- Kinh nghiệm trong lĩnh vực e-commerce hoặc fintech là lợi thế""",
            "benefit": """- Tiếp cận dữ liệu thực tế quy mô lớn của sàn TMĐT top đầu
- Môi trường data-driven, quyết định dựa trên số liệu
- Laptop MacBook, màn hình ngoài
- Team trẻ, năng động, định kỳ team building
- Lương review hàng năm theo năng lực""",
        },
    ],
    "0400112233": [  # Axon Active
        {
            "title": "Full Stack Developer (.NET + Angular)",
            "category_name": "Software Development",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.MIDDLE,
            "status": Job.Status.PUBLISHED,
            "address": "Lầu 7, Tòa nhà Etown 2, 364 Cộng Hòa, Quận Tân Bình, TP. Hồ Chí Minh",
            "salary_min": 28_000_000,
            "salary_max": 50_000_000,
            "salary_currency": "VND",
            "expired_at_days": 30,
            "description": """Axon Active Vietnam tìm kiếm Full Stack Developer để phát triển phần mềm doanh nghiệp cho khách hàng Thụy Sĩ trong các lĩnh vực tài chính, bảo hiểm và logistics theo quy trình Agile chuyên nghiệp.""",
            "requirements": """- 2–5 năm kinh nghiệm phát triển phần mềm
- Thành thạo .NET (ASP.NET Core, C#) ở phía backend
- Có kinh nghiệm với Angular (v12+) ở phía frontend
- Hiểu về cơ sở dữ liệu quan hệ (SQL Server, PostgreSQL)
- Kinh nghiệm làm việc trong môi trường Agile/Scrum
- Tiếng Anh đủ để đọc tài liệu và họp với khách hàng nước ngoài""",
            "benefit": """- Làm việc trực tiếp với khách hàng Thụy Sĩ, môi trường quốc tế
- Quy trình Agile chuẩn Swiss, team nhỏ gọn, tự chủ cao
- 15 ngày phép/năm + du lịch công ty hàng năm
- Bảo hiểm sức khỏe, hỗ trợ học phí nâng cao kỹ năng
- WFH linh hoạt, giờ làm việc mềm dẻo""",
        },
        {
            "title": "Scrum Master / Agile Coach",
            "category_name": "IT Project Management",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.SENIOR,
            "status": Job.Status.PUBLISHED,
            "address": "Lầu 7, Tòa nhà Etown 2, 364 Cộng Hòa, Quận Tân Bình, TP. Hồ Chí Minh",
            "salary_min": 35_000_000,
            "salary_max": 60_000_000,
            "salary_currency": "VND",
            "expired_at_days": 45,
            "description": """Axon Active tìm Scrum Master có kinh nghiệm để hỗ trợ nhiều đội Agile, thúc đẩy văn hóa cải tiến liên tục và đảm bảo chất lượng quy trình phát triển phần mềm theo chuẩn Swiss.""",
            "requirements": """- Tối thiểu 3 năm kinh nghiệm ở vai trò Scrum Master
- Có chứng chỉ CSM, PSM I trở lên
- Hiểu sâu về Scrum, Kanban, SAFe
- Kỹ năng facilitation, coaching và giải quyết xung đột tốt
- Tiếng Anh thành thạo (giao tiếp hàng ngày với khách hàng nước ngoài)
- Ưu tiên ứng viên có nền tảng kỹ thuật (từng là developer)""",
            "benefit": """- Đồng hành cùng đội ngũ Agile từ Thụy Sĩ, học hỏi best practices quốc tế
- Hỗ trợ thi các chứng chỉ Agile cấp cao (A-CSM, PSM II, SAFe)
- Lương hấp dẫn, review định kỳ
- Môi trường làm việc tin tưởng và trao quyền tối đa""",
        },
    ],
    "0500223344": [  # NashTech
        {
            "title": "Security Engineer (Penetration Tester)",
            "category_name": "Information Security",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.MIDDLE,
            "status": Job.Status.PUBLISHED,
            "address": "Lầu 9, Tòa nhà Viettel, 285 Cách Mạng Tháng 8, Quận 10, TP. Hồ Chí Minh",
            "salary_min": 30_000_000,
            "salary_max": 55_000_000,
            "salary_currency": "VND",
            "expired_at_days": 30,
            "description": """NashTech cần Security Engineer thực hiện đánh giá bảo mật, kiểm tra xâm nhập và tư vấn giải pháp bảo mật cho các khách hàng doanh nghiệp trong và ngoài nước.""",
            "requirements": """- 2–5 năm kinh nghiệm về bảo mật thông tin
- Thành thạo penetration testing (web, mobile, network)
- Hiểu biết về OWASP Top 10, CVE, các kỹ thuật exploit phổ biến
- Sử dụng thành thạo Burp Suite, Metasploit, Nmap, Nessus
- Có chứng chỉ CEH, OSCP, hoặc tương đương là lợi thế lớn
- Kỹ năng viết báo cáo pentest rõ ràng, chuyên nghiệp""",
            "benefit": """- Tiếp cận đa dạng hệ thống từ nhiều ngành: ngân hàng, TMĐT, chính phủ
- Hỗ trợ học và thi chứng chỉ bảo mật quốc tế (OSCP, CISSP)
- Môi trường làm việc chuyên nghiệp theo tiêu chuẩn Harvey Nash Group
- Chính sách remote linh hoạt
- Bảo hiểm sức khỏe, thưởng hiệu suất hàng quý""",
        },
        {
            "title": "UI/UX Designer",
            "category_name": "UI/UX Design",
            "employment_type": Job.EmploymentType.FULL_TIME,
            "experience_level": Job.ExperienceLevel.JUNIOR,
            "status": Job.Status.DRAFT,
            "address": "Lầu 9, Tòa nhà Viettel, 285 Cách Mạng Tháng 8, Quận 10, TP. Hồ Chí Minh",
            "salary_min": 15_000_000,
            "salary_max": 25_000_000,
            "salary_currency": "VND",
            "expired_at_days": 60,
            "description": """NashTech tìm kiếm UI/UX Designer để thiết kế giao diện và trải nghiệm người dùng cho các sản phẩm phần mềm B2B phục vụ khách hàng UK và châu Âu.""",
            "requirements": """- 1–3 năm kinh nghiệm UI/UX Design
- Thành thạo Figma (thiết kế, prototyping, design system)
- Hiểu biết về user research, usability testing
- Có portfolio thể hiện rõ quy trình design thinking
- Tiếng Anh đọc hiểu tốt để làm việc với tài liệu và khách hàng quốc tế
- Kiến thức cơ bản về HTML/CSS là điểm cộng""",
            "benefit": """- Làm việc trong môi trường quốc tế, sản phẩm B2B đa lĩnh vực
- Được đào tạo và hướng dẫn bởi senior designer người nước ngoài
- Ngân sách mua tool design (Figma, Adobe CC...)
- Giờ làm linh hoạt, văn phòng trung tâm thành phố""",
        },
    ],
}


class Command(BaseCommand):
    help = "Seed job data for existing companies and categories"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all seeded jobs before re-seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            tax_codes = list(JOBS_DATA.keys())
            deleted, _ = Job.objects.filter(company__tax_code__in=tax_codes).delete()
            self.stdout.write(self.style.WARNING(f"Đã xóa {deleted} job(s) cũ."))

        total_created = 0
        total_skipped = 0

        for tax_code, jobs in JOBS_DATA.items():
            try:
                company = Company.objects.get(tax_code=tax_code)
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"Không tìm thấy công ty với tax_code={tax_code}. Bỏ qua."
                ))
                continue

            self.stdout.write(f"\n🏢 {company.name}")

            for job_data in jobs:
                category = Category.objects.filter(name=job_data["category_name"]).first()
                if not category:
                    self.stdout.write(self.style.WARNING(
                        f"Category '{job_data['category_name']}' không tồn tại. Job sẽ không có category."
                    ))

                now = timezone.now()
                expired_at = now + timedelta(days=job_data.pop("expired_at_days"))
                category_name = job_data.pop("category_name")
                company_location = company.locations.filter(is_primary=True).first() or company.locations.first()
                address = company_location.address if company_location else None

                job, created = Job.objects.get_or_create(
                    title=job_data["title"],
                    company=company,
                    defaults={
                        **{k: v for k, v in job_data.items()},
                        "category": category,
                        "expired_at": expired_at,
                        "address": address,
                        "published_at": now,
                    },
                )

                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"[{job.employment_type}] {job.title} ({job.experience_level}) — {job.status}"
                    ))
                else:
                    total_skipped += 1
                    self.stdout.write(
                        f"   — Bỏ qua (đã tồn tại): {job.title}"
                    )

                job_data["category_name"] = category_name

        from django.contrib.postgres.search import SearchVector
        from django.db.models import Value

        for job in Job.objects.filter(company__tax_code__in=JOBS_DATA.keys()):
            Job.objects.filter(pk=job.pk).update(
                search_vector=(
                        SearchVector(Value(job.title), weight='A', config='simple') +
                        SearchVector(Value(job.company.name), weight='A', config='simple') +
                        SearchVector(Value(job.description or ""), weight='B', config='simple') +
                        SearchVector(Value(job.requirements or ""), weight='C', config='simple')
                )
            )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(
            f"Hoàn tất! Tạo mới: {total_created} job(s). Bỏ qua: {total_skipped} job(s)."
        ))
        self.stdout.write("=" * 50 + "\n")
