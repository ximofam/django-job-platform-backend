#!/bin/sh

set -e

# 1. NẠP FILE .env VÀO MÔI TRƯỜNG SHELL
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# 2. XÓA TOÀN BỘ DỮ LIỆU CŨ (FLUSH)
echo "Wiping out old database data..."
python manage.py flush --no-input

# 3. CHẠY MIGRATIONS ĐỂ ĐẢM BẢO CẤU TRÚC DB ĐƯỢC CẬP NHẬT
echo "Running migrations..."
python manage.py migrate --noinput

# 4. CHẠY SEED DATA MỚI
echo "Seeding data..."
python manage.py seed_countries
python manage.py seed_location
python manage.py seed_roles
python manage.py seed_employers
python manage.py seed_categories
python manage.py seed_jobs
python manage.py setup_gotify_account

# 5. TẠO LẠI SUPERUSER (Vì lệnh flush đã xóa cả user)
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

# Các biến này giờ sẽ lấy được giá trị từ file .env nhờ lệnh export ở trên
username = '${DJANGO_SUPERUSER_USERNAME:-admin}'
email = '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}'
password = '${DJANGO_SUPERUSER_PASSWORD:-admin123}'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser \"{username}\" created.')
else:
    print(f'Superuser \"{username}\" already exists, skipping.')
"

#echo "Collecting static files..."
#python manage.py collectstatic --noinput

echo "========================================"
read -p "Tất cả lệnh đã chạy xong. Bấm [Enter] để tiếp tục"
echo "========================================"
#
#echo "Starting Gunicorn..."
#exec gunicorn config.wsgi:application \
#    --bind 0.0.0.0:8000