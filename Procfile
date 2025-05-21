web: gunicorn lynkledger_api.wsgi:application --bind 0.0.0.0:8000
worker: celery -A lynkledger_api worker -l info
beat: celery -A lynkledger_api beat -l info 