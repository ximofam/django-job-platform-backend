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

echo "========================================"
echo "Creating superuser..."
echo "========================================"
python manage.py createsuperuser --noinput || echo "Superuser đã tồn tại hoặc thiếu biến môi trường, bỏ qua tạo mới."

echo "========================================"
echo "Setting up OAuth Application..."
echo "========================================"
python manage.py setup_oauth

#echo "Collecting static files..."
#python manage.py collectstatic --noinput

echo "========================================"
read -p "Tất cả lệnh đã chạy xong. Bấm [Enter] để tiếp tục"
echo "========================================"
#
#echo "Starting Gunicorn..."
#exec gunicorn config.wsgi:application \
#    --bind 0.0.0.0:8000