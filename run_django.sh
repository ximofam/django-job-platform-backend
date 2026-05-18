#!/bin/sh

set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding data..."
python manage.py seed_countries
python manage.py seed_location
python manage.py seed_roles
python manage.py seed_employers
python manage.py seed_categories
python manage.py seed_jobs

echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
username = '${DJANGO_SUPERUSER_USERNAME:-admin}'
email = '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}'
password = '${DJANGO_SUPERUSER_PASSWORD:-admin123}'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser \"{username}\" created.')
else:
    print(f'Superuser \"{username}\" already exists, skipping.')
"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000