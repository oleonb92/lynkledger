FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        python3-dev \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create static and media directories
RUN mkdir -p /app/staticfiles \
    && mkdir -p /app/media \
    && chmod -R 755 /app/staticfiles \
    && chmod -R 755 /app/media

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create a non-root user
RUN useradd -m myuser \
    && chown -R myuser:myuser /app

# Switch to non-root user
USER myuser

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
