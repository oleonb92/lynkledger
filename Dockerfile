# FROM python:3.11-slim

# WORKDIR /app

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# RUN apt-get update \
#     && apt-get install -y --no-install-recommends gcc libpq-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Recolecta archivos estáticos al hacer build (opcionalmente podrías usar un comando separado)
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Usa Gunicorn (servidor de producción más robusto que runserver)
CMD ["gunicorn", "lynkledger_api.wsgi:application", "--bind", "0.0.0.0:8000"]
