from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone

from apps.users.models import User, Company, EmployerProfile, CompanyLocation
from apps.locations.models import Country, City, District, Address

COMPANIES_DATA = [
    {
        "name": "FPT Software",
        "type": Company.Type.OUTSOURCE,
        "employee_size": Company.EmployeeSize.ENTERPRISE,
        "tax_code": "0101248141",
        "description": "FPT Software là công ty công nghệ hàng đầu Việt Nam, cung cấp dịch vụ gia công phần mềm toàn cầu.",
        "locations": [
            {
                "city_name": "Thành phố Hà Nội",
                "district_name": "Quận Cầu Giấy",
                "street_address": "Tòa nhà FPT, 17 Duy Tân",
                "label": CompanyLocation.Label.HEADQUARTERS,
                "is_primary": True,
            },
            {
                "city_name": "Thành phố Hồ Chí Minh",
                "district_name": "Quận 7",
                "street_address": "Lô E2a-7, Đường D1, Khu Công nghệ cao",
                "label": CompanyLocation.Label.BRANCH,
                "is_primary": False,
            },
            {
                "city_name": "Thành phố Đà Nẵng",
                "district_name": "Quận Hải Châu",
                "street_address": "Tòa nhà FPT Complex, 30 Trần Phú",
                "label": CompanyLocation.Label.BRANCH,
                "is_primary": False,
            },
        ],
    },
    {
        "name": "VNG Corporation",
        "type": Company.Type.PRODUCT,
        "employee_size": Company.EmployeeSize.VERY_LARGE,
        "tax_code": "0303456789",
        "description": "VNG là công ty công nghệ tiên phong tại Việt Nam với các sản phẩm nổi tiếng như Zalo, ZaloPay.",
        "locations": [
            {
                "city_name": "Thành phố Hồ Chí Minh",
                "district_name": "Quận 7",
                "street_address": "Vạn Phúc City, 1 Đường số 8, Phường Hiệp Bình Phước",
                "label": CompanyLocation.Label.HEADQUARTERS,
                "is_primary": True,
            },
            {
                "city_name": "Thành phố Hà Nội",
                "district_name": "Quận Cầu Giấy",
                "street_address": "Tầng 10, Toà nhà Viwaseen, 48 Tố Hữu",
                "label": CompanyLocation.Label.BRANCH,
                "is_primary": False,
            },
        ],
    },
    {
        "name": "Tiki Corporation",
        "type": Company.Type.PRODUCT,
        "employee_size": Company.EmployeeSize.LARGE,
        "tax_code": "0312345678",
        "description": "Tiki là nền tảng thương mại điện tử hàng đầu Việt Nam, cam kết mang lại trải nghiệm mua sắm tốt nhất.",
        "locations": [
            {
                "city_name": "Thành phố Hồ Chí Minh",
                "district_name": "Quận 1",
                "street_address": "52 Út Tịch, Phường 4",
                "label": CompanyLocation.Label.HEADQUARTERS,
                "is_primary": True,
            },
        ],
    },
    {
        "name": "Axon Active Vietnam",
        "type": Company.Type.OUTSOURCE,
        "employee_size": Company.EmployeeSize.MEDIUM,
        "tax_code": "0400112233",
        "description": "Axon Active là công ty phần mềm Thụy Sĩ với văn phòng tại Việt Nam, chuyên phát triển phần mềm Agile.",
        "locations": [
            {
                "city_name": "Thành phố Hồ Chí Minh",
                "district_name": "Quận 1",
                "street_address": "Tầng 8, Tòa nhà Viet Dragon, 141 Nguyễn Huệ",
                "label": CompanyLocation.Label.HEADQUARTERS,
                "is_primary": True,
            },
            {
                "city_name": "Thành phố Đà Nẵng",
                "district_name": "Quận Hải Châu",
                "street_address": "Tầng 7, Tòa nhà Indochina Riverside, 74 Bạch Đằng",
                "label": CompanyLocation.Label.BRANCH,
                "is_primary": False,
            },
        ],
    },
    {
        "name": "NashTech Vietnam",
        "type": Company.Type.OUTSOURCE,
        "employee_size": Company.EmployeeSize.LARGE,
        "tax_code": "0500223344",
        "description": "NashTech là công ty công nghệ thuộc tập đoàn Harvey Nash, chuyên cung cấp giải pháp phần mềm.",
        "locations": [
            {
                "city_name": "Thành phố Hồ Chí Minh",
                "district_name": "Quận 3",
                "street_address": "Tầng 9, Tòa nhà E-Town 2, 364 Cộng Hòa",
                "label": CompanyLocation.Label.HEADQUARTERS,
                "is_primary": True,
            },
            {
                "city_name": "Thành phố Hà Nội",
                "district_name": "Quận Đống Đa",
                "street_address": "Tầng 5, Tòa nhà Icon4, 243A Đê La Thành",
                "label": CompanyLocation.Label.BRANCH,
                "is_primary": False,
            },
        ],
    },
]

EMPLOYERS_DATA = [
    {
        "username": "employer_fpt",
        "email": "employer@fpt-software.com",
        "first_name": "Minh",
        "last_name": "Nguyen",
        "password": "Employer@123",
        "gender": User.Gender.MALE,
        "company_index": 0,
        "status": EmployerProfile.Status.APPROVED,
    },
    {
        "username": "employer_vng",
        "email": "employer@vng.com.vn",
        "first_name": "Lan",
        "last_name": "Tran",
        "password": "Employer@123",
        "gender": User.Gender.FEMALE,
        "company_index": 1,
        "status": EmployerProfile.Status.APPROVED,
    },
    {
        "username": "employer_tiki",
        "email": "employer@tiki.vn",
        "first_name": "Huy",
        "last_name": "Le",
        "password": "Employer@123",
        "gender": User.Gender.MALE,
        "company_index": 2,
        "status": EmployerProfile.Status.PENDING,
    },
    {
        "username": "employer_axon",
        "email": "employer@axonactive.com",
        "first_name": "Linh",
        "last_name": "Pham",
        "password": "Employer@123",
        "gender": User.Gender.FEMALE,
        "company_index": 3,
        "status": EmployerProfile.Status.APPROVED,
    },
    {
        "username": "employer_nash",
        "email": "employer@nashtech.com",
        "first_name": "Duc",
        "last_name": "Vo",
        "password": "Employer@123",
        "gender": User.Gender.MALE,
        "company_index": 4,
        "status": EmployerProfile.Status.DENIED,
    },
]


class Command(BaseCommand):
    help = "Seed employer and company data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing employer seed data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing employer seed data...")
            usernames = [e["username"] for e in EMPLOYERS_DATA]
            User.objects.filter(username__in=usernames).delete()
            tax_codes = [c["tax_code"] for c in COMPANIES_DATA]
            Company.objects.filter(tax_code__in=tax_codes).delete()
            self.stdout.write(self.style.WARNING("Cleared."))

        employer_group, _ = Group.objects.get_or_create(name=User.Role.EMPLOYER)

        country = Country.objects.filter(code="VN").first()
        if not country:
            self.stdout.write(self.style.WARNING(
                "Country with code 'VN' not found. Companies will have no country set."
            ))

        admin_user = User.objects.filter(role=User.Role.ADMIN).first()

        companies = []
        for data in COMPANIES_DATA:
            company, created = Company.objects.get_or_create(
                tax_code=data["tax_code"],
                defaults={
                    "name": data["name"],
                    "type": data["type"],
                    "employee_size": data["employee_size"],
                    "description": data["description"],
                    "status": Company.Status.APPROVED,
                    "country": country,
                },
            )
            companies.append(company)
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  Company [{status}]: {company.name}")

            # Seed locations cho company
            for loc_data in data.get("locations", []):
                city = City.objects.filter(name=loc_data["city_name"]).first()
                if not city:
                    self.stdout.write(self.style.WARNING(
                        f"City not found: {loc_data['city_name']} — skipping location"
                    ))
                    continue

                district = District.objects.filter(
                    city=city,
                    name=loc_data["district_name"],
                ).first()
                if not district:
                    self.stdout.write(self.style.WARNING(
                        f"District not found: {loc_data['district_name']} ({city.name}) — skipping location"
                    ))
                    continue

                address, _ = Address.objects.get_or_create(
                    city=city,
                    district=district,
                    street_address=loc_data["street_address"],
                )

                company_location, loc_created = CompanyLocation.objects.get_or_create(
                    company=company,
                    address=address,
                    defaults={
                        "label": loc_data["label"],
                        "is_primary": loc_data["is_primary"],
                    },
                )
                loc_status = "Created" if loc_created else "Already exists"
                self.stdout.write(
                    f"Location [{loc_status}]: {loc_data['label']} — {address}"
                )

        # Create employer users + profiles
        for data in EMPLOYERS_DATA:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "gender": data["gender"],
                    "role": User.Role.EMPLOYER,
                    "is_active": True,
                },
            )
            if created:
                user.set_password(data["password"])
                user.save()
                user.groups.add(employer_group)

            company = companies[data["company_index"]]

            profile, profile_created = EmployerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "company": company,
                    "status": data["status"],
                    "approved_by": admin_user if data["status"] == EmployerProfile.Status.APPROVED else None,
                    "approved_at": timezone.now() if data["status"] == EmployerProfile.Status.APPROVED else None,
                },
            )

            u_status = "Created" if created else "Already exists"
            p_status = "Created" if profile_created else "Already exists"
            self.stdout.write(
                f"  Employer [{u_status}]: {user.get_full_name()} ({user.email}) | "
                f"Profile [{p_status}]: {profile.status} | Company: {company.name}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Seeded {len(EMPLOYERS_DATA)} employers and {len(COMPANIES_DATA)} companies."
        ))
