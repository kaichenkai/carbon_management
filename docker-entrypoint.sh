#!/bin/bash

set -e

echo "Checking database..."

# For SQLite, just ensure the directory exists
mkdir -p /app

# Try to run migrations directly (SQLite doesn't need connection check)
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "Migration failed, retrying in 5 seconds..."
    sleep 5
    python manage.py migrate --noinput
}

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123');
    print('Superuser created successfully');
else:
    print('Superuser already exists');
" || echo "Superuser creation skipped"

echo "Starting Gunicorn..."
exec gunicorn carbon_management.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
