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
    sleep 1
    timeout=$((timeout-1))
done
log "Database is ready!"

# Apply database migrations with error handling
log "Applying database migrations..."
python manage.py migrate --noinput || {
    log "Error: Failed to apply migrations"
    exit 1
}
log "Migrations applied successfully"

# Create superuser if it doesn't exist
log "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
from django.db import connection;
from django.db.utils import OperationalError;
import sys;

User = get_user_model();
try:
    # Test database connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        log('Database connection successful')
    
    # Check if superuser exists
    if not User.objects.filter(username='admin').exists():
        log('Creating new superuser...')
        user = User.objects.create_superuser(
            username='admin',
            email='osmanileon92@gmail.com',
            password='Natali@rca1992'
        )
        log('Superuser created successfully')
        log(f'Username: {user.username}')
        log(f'Email: {user.email}')
        log(f'Is staff: {user.is_staff}')
        log(f'Is superuser: {user.is_superuser}')
        log(f'Is active: {user.is_active}')
        
        # Verify user can be retrieved
        user = User.objects.get(username='admin')
        log('Superuser verification successful')
        log(f'Can authenticate: {user.check_password(\"Natali@rca1992\")}')
    else:
        user = User.objects.get(username='admin')
        log('Superuser already exists')
        log(f'Username: {user.username}')
        log(f'Email: {user.email}')
        log(f'Is staff: {user.is_staff}')
        log(f'Is superuser: {user.is_superuser}')
        log(f'Is active: {user.is_active}')
        
        # Verify password
        if not user.check_password('Natali@rca1992'):
            log('Updating superuser password...')
            user.set_password('Natali@rca1992')
            user.save()
            log('Password updated successfully')
            log(f'Can authenticate: {user.check_password(\"Natali@rca1992\")}')
        else:
            log('Password is correct')
            log(f'Can authenticate: {user.check_password(\"Natali@rca1992\")}')
except Exception as e:
    log(f'Error: {str(e)}')
    log(f'Error type: {type(e).__name__}')
    import traceback
    log(f'Traceback: {traceback.format_exc()}')
    sys.exit(1)
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

log "Setup completed successfully" 