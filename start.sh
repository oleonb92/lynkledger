#!/usr/bin/env bash
# exit on error
set -o errexit

# Start Gunicorn
gunicorn lynkledger_api.wsgi:application --bind 0.0.0.0:8000 