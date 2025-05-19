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