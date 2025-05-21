#!/usr/bin/env bash
# exit on error
set -o errexit

# Start Celery worker
celery -A lynkledger_api worker -l info 