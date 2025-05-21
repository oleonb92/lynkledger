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

# Create superuser if it doesn't exist
log "Checking for superuser..."
if [ -z "$DJANGO_SUPERUSER_USERNAME" ] || [ -z "$DJANGO_SUPERUSER_EMAIL" ] || [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
    log "Error: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD must be set"
    exit 1
fi

# Check if superuser exists
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists()"; then
    log "Creating superuser..."
    python manage.py createsuperuser --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
    log "Superuser created successfully!"
else
    log "Superuser already exists, updating password..."
    python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(username='$DJANGO_SUPERUSER_USERNAME'); user.set_password('$DJANGO_SUPERUSER_PASSWORD'); user.save()"
    log "Superuser password updated!"
fi

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