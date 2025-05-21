#!/bin/bash

# Enable error handling
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Wait for database with timeout
log "Waiting for database..."
timeout=30
while ! nc -z $DB_HOST $DB_PORT; do
    if [ $timeout -le 0 ]; then
        log "Error: Database connection timeout"
        exit 1
    fi
    sleep 0.1
    timeout=$((timeout-1))
done
log "Database is up!"

# Apply database migrations with error handling
log "Applying database migrations..."
python manage.py migrate --noinput || {
    log "Error: Failed to apply migrations"
    exit 1
}
log "Migrations applied successfully"

# Set default superuser values if not provided
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-"admin"}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-"admin@lynkledger.com"}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-"admin123"}

log "Using superuser credentials:"
log "Username: $DJANGO_SUPERUSER_USERNAME"
log "Email: $DJANGO_SUPERUSER_EMAIL"

# Check if superuser exists and create/update it
log "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    user = User.objects.get(username='$DJANGO_SUPERUSER_USERNAME')
    log('Superuser exists, updating...')
    user.set_password('$DJANGO_SUPERUSER_PASSWORD')
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()
    print('Superuser updated successfully!')
except User.DoesNotExist:
    log('Creating new superuser...')
    User.objects.create_superuser(
        username='$DJANGO_SUPERUSER_USERNAME',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    print('Superuser created successfully!')
"

# Verify superuser was created/updated
log "Verifying superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='$DJANGO_SUPERUSER_USERNAME')
print(f'Superuser verification:')
print(f'Username: {user.username}')
print(f'Email: {user.email}')
print(f'Is staff: {user.is_staff}')
print(f'Is superuser: {user.is_superuser}')
print(f'Is active: {user.is_active}')
"

# Ensure static and media directories exist and have correct permissions
log "Setting up static and media directories..."
mkdir -p /app/staticfiles
mkdir -p /app/media
chmod -R 755 /app/staticfiles
chmod -R 755 /app/media

# Collect static files with verbose output
log "Collecting static files..."
python manage.py collectstatic --noinput --clear -v 2 || {
    log "Error: Failed to collect static files"
    exit 1
}

# Verify static files
log "Verifying static files..."
ls -la /app/staticfiles/admin/css/ || {
    log "Error: Static files verification failed"
    exit 1
}

# Start server
log "Starting server..."
gunicorn lynkledger_api.wsgi:application --bind 0.0.0.0:8000

log "Setup completed successfully" 