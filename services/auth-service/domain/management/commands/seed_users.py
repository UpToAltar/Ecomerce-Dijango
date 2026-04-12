from django.core.management.base import BaseCommand
from domain.models import User


class Command(BaseCommand):
    help = 'Seed initial users (admin, staff, customers)'

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true', help='Skip confirmation')

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write(self.style.WARNING('Users already exist, skipping seed.'))
            return

        self.stdout.write('Seeding users...')

        # Admin
        User.objects.create_superuser(
            email='admin@shop.com',
            password='Admin@123',
            first_name='Admin',
            last_name='System',
            phone='0900000001',
            address='123 Admin Street, District 1, Ho Chi Minh City',
        )
        self.stdout.write(self.style.SUCCESS('  ✓ admin@shop.com (admin)'))

        # Staff
        staff_data = [
            {'email': 'staff1@shop.com', 'first_name': 'Nguyen', 'last_name': 'Van A', 'phone': '0900000002'},
            {'email': 'staff2@shop.com', 'first_name': 'Tran', 'last_name': 'Thi B', 'phone': '0900000003'},
        ]
        for data in staff_data:
            User.objects.create_user(
                password='Staff@123',
                role=User.Role.STAFF,
                is_staff=True,
                address='456 Staff Road, District 3, Ho Chi Minh City',
                **data,
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ {data["email"]} (staff)'))

        # Customers
        customers = [
            {'email': 'customer1@gmail.com', 'first_name': 'Le', 'last_name': 'Van C', 'phone': '0911000001',
             'address': '10 Nguyen Hue, District 1, Ho Chi Minh City'},
            {'email': 'customer2@gmail.com', 'first_name': 'Pham', 'last_name': 'Thi D', 'phone': '0911000002',
             'address': '20 Le Loi, District 1, Ho Chi Minh City'},
            {'email': 'customer3@gmail.com', 'first_name': 'Hoang', 'last_name': 'Van E', 'phone': '0911000003',
             'address': '30 Tran Hung Dao, District 5, Ho Chi Minh City'},
            {'email': 'customer4@gmail.com', 'first_name': 'Vo', 'last_name': 'Thi F', 'phone': '0911000004',
             'address': '40 Hai Ba Trung, District 3, Ho Chi Minh City'},
            {'email': 'customer5@gmail.com', 'first_name': 'Dang', 'last_name': 'Van G', 'phone': '0911000005',
             'address': '50 Pham Ngu Lao, District 1, Ho Chi Minh City'},
            {'email': 'customer6@gmail.com', 'first_name': 'Bui', 'last_name': 'Thi H', 'phone': '0911000006',
             'address': '60 Vo Van Tan, District 3, Ho Chi Minh City'},
            {'email': 'customer7@gmail.com', 'first_name': 'Do', 'last_name': 'Van I', 'phone': '0911000007',
             'address': '70 Cach Mang Thang 8, District 10, Ho Chi Minh City'},
        ]
        for data in customers:
            User.objects.create_user(
                password='Customer@123',
                role=User.Role.CUSTOMER,
                **data,
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ {data["email"]} (customer)'))

        self.stdout.write(self.style.SUCCESS(f'\nSeeded {User.objects.count()} users successfully!'))
