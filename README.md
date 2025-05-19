# Lynkledger - Modern Accounting System

Lynkledger is a modern accounting application with advanced features including AI integration, real-time collaboration, and multi-language support.

## Features

- Double-entry accounting system
- Multi-organization support
- Real-time collaboration
- Document management with OCR
- AI-powered assistance
- Multi-language support (English/Spanish)
- Advanced reporting and analytics
- Budget management
- Invoice and payment tracking
- Tax rate management
- Fixed assets tracking
- Recurring transactions

## Requisitos Previos

1. **Software Necesario**:
   - Git ([Descargar](https://git-scm.com/download/win))
   - Docker Desktop ([Descargar](https://www.docker.com/products/docker-desktop))
   - Visual Studio Code (recomendado) ([Descargar](https://code.visualstudio.com/))

2. **Requisitos del Sistema**:
   - Windows 10/11 Pro, Enterprise o Education (64-bit)
   - Mínimo 8GB RAM
   - 10GB espacio libre en disco
   - Virtualización habilitada en BIOS

## Instalación

1. **Clonar el Repositorio**:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd lynkledger
   ```

2. **Configurar Variables de Entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Iniciar en Modo Desarrollo**:
   ```bash
   docker-compose up -d
   ```

4. **Iniciar en Modo Producción**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Crear Superusuario**:
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

## Acceso a la Aplicación

- Frontend: http://localhost:3000
- API: http://localhost:8000/api
- Admin: http://localhost:8000/admin

## Solución de Problemas Comunes

1. **Docker no Inicia**:
   - Verificar que Docker Desktop esté corriendo
   - Verificar que WSL2 esté instalado y actualizado
   - Reiniciar Docker Desktop

2. **Problemas de Permisos**:
   - Ejecutar Docker Desktop como administrador
   - Verificar permisos en carpetas de volúmenes

3. **Problemas de Red**:
   - Verificar que los puertos 3000, 8000 y 5432 estén libres
   - Verificar configuración de firewall

4. **Problemas de Base de Datos**:
   ```bash
   # Reiniciar la base de datos
   docker-compose down -v
   docker-compose up -d
   ```

## Respaldo y Migración

1. **Respaldar Base de Datos**:
   ```bash
   docker-compose exec db pg_dump -U postgres lynkledger > backup.sql
   ```

2. **Restaurar Base de Datos**:
   ```bash
   docker-compose exec -T db psql -U postgres lynkledger < backup.sql
   ```

3. **Respaldar Archivos de Media**:
   ```bash
   zip -r media_backup.zip backend/media/
   ```

## Mantenimiento

1. **Actualizar Dependencias**:
   ```bash
   # Backend
   docker-compose exec backend pip install -r requirements.txt

   # Frontend
   docker-compose exec frontend npm install
   ```

2. **Limpiar Docker**:
   ```bash
   docker-compose down
   docker system prune -a
   ```

## Seguridad

1. **En Desarrollo**:
   - Usar contraseñas seguras en .env
   - No exponer puertos innecesarios
   - Mantener Docker actualizado

2. **En Producción**:
   - Usar docker-compose.prod.yml
   - Configurar HTTPS/SSL
   - Cambiar todas las contraseñas por defecto
   - Configurar backups automáticos

## Soporte

Para soporte técnico:
1. Revisar la documentación en `/docs`
2. Crear un issue en el repositorio
3. Contactar al equipo de desarrollo

## Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Crear Pull Request

## Project Structure

```
lynkledger/
├── backend/           # Django backend
│   ├── accounting/    # Core accounting functionality
│   ├── users/         # User management
│   ├── organizations/ # Organization management
│   ├── documents/     # Document management
│   ├── messaging/     # Real-time messaging
│   ├── notifications/ # User notifications
│   └── ai_assistant/  # AI integration
├── frontend/          # React frontend
├── nginx/            # Nginx configuration
└── postgres/         # PostgreSQL data
```

## Development

### Backend Development

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Start development server:
   ```bash
   python manage.py runserver
   ```

### Frontend Development

1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start development server:
   ```bash
   npm start
   ```

## Testing

### Backend Tests
```bash
docker-compose exec backend python manage.py test
```

### Frontend Tests
```bash
docker-compose exec frontend npm test
```

## Deployment

1. Update `.env` file with production settings
2. Build production images:
   ```bash
   docker-compose -f docker-compose.prod.yml build
   ```
3. Deploy containers:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Security Considerations

- Change all default passwords in production
- Use strong SECRET_KEY in Django settings
- Configure proper ALLOWED_HOSTS
- Enable HTTPS in production
- Set up proper backup strategy
- Configure proper file storage (e.g., AWS S3)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact support@lynkledger.com 