# Use the official Python image as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=lynkledger_api.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nginx \
        postgresql-client \
        build-essential \
        libpq-dev \
        python3-dev \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY backend /app/

# Copy Nginx configuration
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy supervisord configuration
COPY supervisord.conf /app/supervisord.conf

# Create necessary directories and set permissions
RUN mkdir -p /app/staticfiles /app/media \
    && chmod -R 755 /app/staticfiles /app/media

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Run as non-root user
RUN useradd -m myuser \
    && chown -R myuser:myuser /app
USER myuser

# Expose ports
EXPOSE 80 8000

# Command to run on container start
CMD ["/usr/local/bin/supervisord", "-c", "/app/supervisord.conf"] 