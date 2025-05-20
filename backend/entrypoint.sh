#!/bin/bash

# Wait for database
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Database is ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'osmanileon92@gmail.com', 'Natali@rca1992')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

# Ensure static and media directories exist and have correct permissions
echo "Setting up static and media directories..."
mkdir -p /app/staticfiles
mkdir -p /app/media
chmod -R 755 /app/staticfiles
chmod -R 755 /app/media

# Collect static files with verbose output
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear -v 2

# Verify static files
echo "Verifying static files..."
ls -la /app/staticfiles/admin/css/

# Start Gunicorn with static files serving
echo "Starting Gunicorn..."
exec gunicorn lynkledger_api.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --access-logfile - \
    --error-logfile - \
    --log-level info 