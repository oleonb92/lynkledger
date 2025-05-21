#!/usr/bin/env bash
# exit on error
set -o errexit

# Start Celery beat
celery -A lynkledger_api beat -l info 