#!/bin/bash

# Enable error handling and verbose output
set -ex

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Print environment variables (excluding sensitive ones)
log "Environment variables:"
env | grep -v "PASSWORD\|SECRET\|KEY" | sort

# Wait for postgres to be ready
log "Waiting for postgres to be ready..."
timeout=30
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "postgres" -c '\q'; do
    if [ $timeout -le 0 ]; then
        log "Error: Database connection timeout"
        exit 1
    fi
    log "Postgres is unavailable - sleeping"
    sleep 1
    timeout=$((timeout-1))
done
log "Postgres is up"

# Create database if it doesn't exist
log "Creating database if it doesn't exist..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "postgres" -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE DATABASE $POSTGRES_DB"
log "Database check/creation completed"

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
    print('Superuser exists, updating...')
    user.set_password('$DJANGO_SUPERUSER_PASSWORD')
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()
    print('Superuser updated successfully!')
except User.DoesNotExist:
    print('Creating new superuser...')
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

log "Setup completed successfully"

# Start server
exec gunicorn lynkledger_api.wsgi:application --bind 0.0.0.0:8000 --log-level debug 