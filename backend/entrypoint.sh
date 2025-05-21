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
try:
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser(
            username='admin',
            email='osmanileon92@gmail.com',
            password='Natali@rca1992'
        )
        print('Superuser created successfully')
        print(f'Username: {user.username}')
        print(f'Email: {user.email}')
        print(f'Is staff: {user.is_staff}')
        print(f'Is superuser: {user.is_superuser}')
    else:
        user = User.objects.get(username='admin')
        print('Superuser already exists')
        print(f'Username: {user.username}')
        print(f'Email: {user.email}')
        print(f'Is staff: {user.is_staff}')
        print(f'Is superuser: {user.is_superuser}')
except Exception as e:
    print(f'Error creating superuser: {str(e)}')
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