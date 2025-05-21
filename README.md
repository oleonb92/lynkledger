# Lynkledger

Sistema de gestión financiera y contabilidad empresarial moderno y eficiente.

## Descripción

Lynkledger es una aplicación web completa para la gestión financiera y contable de empresas, construida con tecnologías modernas y siguiendo las mejores prácticas de desarrollo.

## Tecnologías Principales

- **Backend**: Django 4.2.10, Django REST Framework
- **Frontend**: React, TypeScript
- **Base de Datos**: PostgreSQL 15
- **Cache**: Redis
- **Proxy Inverso**: Nginx
- **Contenedorización**: Docker, Docker Compose

## Requisitos

- Docker
- Docker Compose

## Instalación y Configuración

1. Clona el repositorio:
```bash
git clone https://github.com/yourusername/lynkledger.git
cd lynkledger
```

2. Crea un archivo `.env` en la raíz del proyecto (usa `.env.example` como referencia)

3. Construye e inicia los servicios:
```bash
docker compose up -d --build
```

4. Aplica las migraciones:
```bash
docker compose exec backend python manage.py migrate
```

5. Crea un superusuario (opcional):
```bash
docker compose exec backend python manage.py createsuperuser
```

## Acceso a la Aplicación

- **Frontend**: http://localhost
- **API Backend**: http://localhost/api
- **Admin Django**: http://localhost/admin
- **Health Check**: http://localhost/api/health-check

## Desarrollo

### Estructura del Proyecto
```
lynkledger/
├── backend/             # Aplicación Django
├── frontend/           # Aplicación React
├── nginx/              # Configuración de Nginx
└── docker-compose.yml  # Configuración de servicios
```

### Monitoreo de Logs en Desarrollo

Para monitorear los logs de los diferentes servicios en tiempo real, puedes usar los siguientes comandos en terminales separadas:

#### Backend (Django)
```bash
docker compose logs backend -f
```
Esto mostrará:
- Errores de Python/Django
- Peticiones HTTP recibidas
- Mensajes de debug
- Estado de las migraciones
- Cambios en archivos (auto-reload)

#### Frontend (React)
```bash
docker compose logs frontend -f
```
Esto mostrará:
- Compilación de webpack
- Errores de JavaScript/TypeScript
- Hot-reload status
- Problemas de dependencias
- Mensajes de consola del navegador

#### Base de Datos (PostgreSQL)
```bash
docker compose logs db -f
```

#### Redis
```bash
docker compose logs redis -f
```

#### Nginx
```bash
docker compose logs nginx -f
```

#### Todos los servicios
```bash
docker compose logs -f
```

### Comandos Útiles

#### Detener los Servicios
```bash
# Detener todos los servicios
docker compose down

# Detener un servicio específico
docker compose stop <service_name>
```

#### Reiniciar Servicios
```bash
# Reiniciar todos los servicios
docker compose restart

# Reiniciar un servicio específico
docker compose restart <service_name>
```

#### Ejecutar Comandos
```bash
# Ejecutar comando en el backend
docker compose exec backend python manage.py <command>

# Ejecutar comando en el frontend
docker compose exec frontend npm <command>
```

## Testing

```bash
# Ejecutar tests del backend
docker compose exec backend python manage.py test

# Ejecutar tests del frontend
docker compose exec frontend npm test
```

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

[Tipo de Licencia] - ver archivo LICENSE.md para más detalles 


Despliegue en Producción con Render
Lynkledger está diseñado para ejecutarse en Render, una plataforma de alojamiento moderna que se encarga automáticamente del aprovisionamiento, construcción y despliegue de los servicios.

Objetivo de Render
El objetivo principal es que Render maneje la mayor parte de la infraestructura, incluyendo:

Construcción automática de imágenes Docker desde el repositorio.

Ejecución y escalado automático de los contenedores.

Servir el frontend (React) y el backend (Django) desde una misma instancia.

Recolección de archivos estáticos (collectstatic) en cada despliegue.

Supervisión, logs y reinicios automáticos de servicios.

Mínima dependencia de recursos locales (tu computadora no necesita ejecutar nada pesado).

Requisitos en Render
Conecta tu repositorio de GitHub a Render.

Crea un servicio Web (Web Service) con Dockerfile personalizado.

Configura las variables de entorno desde el panel de Render, en vez de usar .env local.

Asegúrate de que tu entrypoint.sh:

Ejecute migraciones (migrate)

Cree el superusuario si no existe

Recoja archivos estáticos (collectstatic)

Arranque Gunicorn y el servidor

Buenas Prácticas
Render detecta automáticamente la apertura del puerto 8000, asegúrate de no hardcodear localhost.

Los archivos estáticos deben servirse desde el backend o configurarse para servir directamente desde Nginx si se usa como reverse proxy.

Usa la rama main para despliegues automáticos (o configura otra rama como producción).

Asegúrate de que todos los servicios estén definidos correctamente en tu Dockerfile, docker-compose, y default.conf.

Render Enviroments:
ALLOWED_HOSTS=lynkledger-backend.onrender.com
CSRF_TRUSTED_ORIGINS=https://lynkledger-backend.onrender.com
CORS_ALLOWED_ORIGINS=https://lynkledger-frontend.onrender.com
DATABASE_URL=postgresql://lynkledger_db_user:BKKEiSlvmpWwrydtigpNZFtcGYv8ZvVy@dpg-d0lrdummcj7s7388t2tg-a/lynkledger_db
DEBUG=False
DJANGO_SETTINGS_MODULE=lynkledger_api.settings
MEDIA_ROOT=/app/media
MEDIA_URL=/media/
SECRET_KEY=<nueva_clave_generada>
SITE_URL=https://lynkledger-backend.onrender.com
STATIC_ROOT=/app/staticfiles
STATIC_URL=/static/
REDIS_HOST=redis
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0