# LynkLedger

LynkLedger is a comprehensive accounting and financial management system built with Django and React.

## Features

- User authentication and authorization
- Organization management
- Accounting and financial tracking
- Real-time notifications
- Email notifications
- API documentation with Swagger/ReDoc
- Celery for background tasks
- Redis for caching and session management

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Node.js 14+
- npm or yarn

## Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```env
# Django settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,*.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com

# Database settings
DATABASE_URL=postgres://user:password@host:port/dbname

# Redis settings
REDIS_URL=redis://user:password@host:port

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Admin settings
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password

# Security settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/oleonb92/lynkledger.git
cd lynkledger
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

3. Set up the frontend:
```bash
cd frontend
npm install
npm start
```

## Development

### Backend

- Run tests: `python manage.py test`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Start Celery worker: `celery -A lynkledger_api worker -l info`
- Start Celery beat: `celery -A lynkledger_api beat -l info`

### Frontend

- Run tests: `npm test`
- Build for production: `npm run build`
- Start development server: `npm start`

## Deployment

### Backend (Render)

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn lynkledger_api.wsgi:application --bind 0.0.0.0:8000`
4. Add environment variables from `.env.example`
5. Deploy

### Frontend (Vercel)

1. Create a new project on Vercel
2. Connect your GitHub repository
3. Set the following:
   - Framework Preset: Create React App
   - Build Command: `npm run build`
   - Output Directory: `build`
4. Add environment variables
5. Deploy

## API Documentation

- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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