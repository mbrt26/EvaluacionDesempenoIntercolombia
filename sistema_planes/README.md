# Sistema de Gestión de Planes de Mejoramiento
## Intercolombia S.A. E.S.P.

Sistema web para la gestión de planes de mejoramiento de proveedores, eliminando la dependencia del formato rígido de correo electrónico y proporcionando transparencia total del proceso.

---

## 📋 Características Principales

- ✅ **Portal Web para Proveedores**: Acceso directo sin formato de correo
- ✅ **Panel de Técnicos**: Revisión y aprobación de planes
- ✅ **Transparencia Total**: Estados visibles en tiempo real
- ✅ **Gestión de Documentos**: Carga y descarga de archivos
- ✅ **Historial Completo**: Trazabilidad de todos los cambios

---

## 🚀 Instalación Rápida

### Requisitos Previos

- Python 3.11 o superior
- PostgreSQL 14 o superior
- Git

### Paso 1: Clonar el Repositorio

```bash
cd /Volumes/Indunnova/CODE/EvaluacionDesempeñoIntercolombia/
cd sistema_planes
```

### Paso 2: Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Mac/Linux:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Configurar Base de Datos

#### Opción A: PostgreSQL (Recomendado para producción)

1. Crear base de datos en PostgreSQL:
```sql
CREATE DATABASE planes_mejoramiento;
CREATE USER planes_user WITH PASSWORD 'planes123';
GRANT ALL PRIVILEGES ON DATABASE planes_mejoramiento TO planes_user;
```

2. Crear archivo `.env` en la raíz del proyecto:
```env
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=planes_mejoramiento
DB_USER=planes_user
DB_PASSWORD=planes123
DB_HOST=localhost
DB_PORT=5432
```

#### Opción B: SQLite (Solo para desarrollo/pruebas)

Modificar `config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Paso 5: Aplicar Migraciones

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

### Paso 6: Crear Datos de Prueba

```bash
# Ejecutar script de datos de prueba
python manage.py shell < crear_datos_prueba.py
```

### Paso 7: Crear Carpetas de Media y Static

```bash
mkdir -p media/planes/documentos
mkdir -p static
mkdir -p staticfiles
```

### Paso 8: Iniciar el Servidor

```bash
python manage.py runserver
```

El sistema estará disponible en: http://localhost:8000/

---

## 👤 Credenciales de Acceso (Datos de Prueba)

### Superusuario (Admin Django)
- **Usuario**: admin
- **Contraseña**: admin123
- **Acceso**: http://localhost:8000/admin/

### Técnicos
- **Usuario**: tecnico1
- **Contraseña**: admin123

- **Usuario**: tecnico2
- **Contraseña**: admin123

### Proveedores
| Empresa | Usuario (NIT) | Contraseña |
|---------|---------------|------------|
| Suministros Industriales ABC | 900123456 | proveedor123 |
| Logística y Transportes XYZ | 900234567 | proveedor123 |
| Servicios Técnicos 123 | 900345678 | proveedor123 |
| Comercializadora DEF | 900456789 | proveedor123 |
| Ingeniería y Consultoría GHI | 900567890 | proveedor123 |

---

## 📱 Uso del Sistema

### Para Proveedores

1. **Ingresar al sistema**: Use su NIT como usuario
2. **Ver evaluación**: Dashboard muestra evaluación actual y estado
3. **Crear plan**: Si puntaje < 80, puede crear plan de mejoramiento
4. **Seguimiento**: Ver estado actual, comentarios del técnico
5. **Ajustes**: Si se requieren ajustes, puede editar y reenviar

### Para Técnicos

1. **Panel de control**: Vista general de planes pendientes
2. **Revisar planes**: Click en "Revisar" para ver detalle
3. **Tomar decisión**: Aprobar, solicitar ajustes o rechazar
4. **Comentarios**: Agregar observaciones para el proveedor

---

## 🛠️ Configuración Adicional

### Variables de Entorno (.env)

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DB_NAME=planes_mejoramiento
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### Configuración para Producción

1. **Desactivar DEBUG**:
```python
DEBUG = False
```

2. **Configurar ALLOWED_HOSTS**:
```python
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
```

3. **Servir archivos estáticos**:
```bash
python manage.py collectstatic
```

4. **Usar Gunicorn**:
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## 📁 Estructura del Proyecto

```
sistema_planes/
├── config/                 # Configuración del proyecto
│   ├── settings.py        # Configuración Django
│   ├── urls.py           # URLs principales
│   └── wsgi.py          # WSGI para producción
├── planes/               # Aplicación principal
│   ├── models.py        # Modelos de datos
│   ├── views.py         # Vistas/Controladores
│   ├── forms.py         # Formularios
│   ├── urls.py          # URLs de la app
│   ├── admin.py         # Configuración admin
│   └── templates/       # Templates HTML
├── templates/           # Templates base
├── static/             # Archivos estáticos
├── media/              # Archivos subidos
├── requirements.txt    # Dependencias
├── manage.py          # Script de gestión Django
└── crear_datos_prueba.py  # Script datos de prueba
```

---

## 🐛 Solución de Problemas Comunes

### Error: "No module named 'psycopg2'"
```bash
# Mac:
brew install postgresql
pip install psycopg2-binary

# Ubuntu/Debian:
sudo apt-get install python3-dev libpq-dev
pip install psycopg2

# Windows:
pip install psycopg2-binary
```

### Error: "FATAL: password authentication failed"
Verificar credenciales en `.env` y permisos en PostgreSQL:
```sql
ALTER USER planes_user WITH PASSWORD 'nueva_password';
```

### Error: "Permission denied" en media/static
```bash
chmod -R 755 media/
chmod -R 755 static/
```

### Error: "Django.core.exceptions.ImproperlyConfigured"
Asegurarse de que el archivo `.env` existe y tiene todas las variables necesarias.

---

## 🚀 Despliegue en Producción

### Opción 1: Servidor VPS con Nginx + Gunicorn

1. **Instalar dependencias**:
```bash
sudo apt update
sudo apt install python3-pip python3-venv postgresql nginx
```

2. **Configurar Nginx**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/sistema_planes/staticfiles/;
    }

    location /media/ {
        alias /path/to/sistema_planes/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Crear servicio systemd**:
```ini
[Unit]
Description=Planes Mejoramiento
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/sistema_planes
ExecStart=/path/to/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

### Opción 2: Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Opción 3: Azure App Service

```bash
# Crear Web App
az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name planes-mejoramiento --runtime "PYTHON|3.11"

# Configurar variables
az webapp config appsettings set --resource-group myResourceGroup --name planes-mejoramiento --settings SECRET_KEY="your-key" DEBUG="False"

# Desplegar
az webapp deployment source config --name planes-mejoramiento --resource-group myResourceGroup --repo-url https://github.com/your-repo --branch main
```

---

## 📊 Monitoreo y Mantenimiento

### Logs
```bash
# Ver logs de Django
tail -f logs/django.log

# Ver logs de Gunicorn
journalctl -u gunicorn -f

# Ver logs de Nginx
tail -f /var/log/nginx/error.log
```

### Backup de Base de Datos
```bash
# Crear backup
pg_dump planes_mejoramiento > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql planes_mejoramiento < backup_20240101.sql
```

### Actualización del Sistema
```bash
# Activar entorno virtual
source venv/bin/activate

# Actualizar código
git pull origin main

# Instalar nuevas dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Recolectar estáticos
python manage.py collectstatic --noinput

# Reiniciar servicio
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 📞 Soporte

Para soporte técnico o preguntas sobre el sistema:
- **Email**: soporte@intercolombia.com
- **Documentación**: Ver carpeta `/docs`

---

## 📄 Licencia

Sistema desarrollado para Intercolombia S.A. E.S.P. - Todos los derechos reservados.

---

## 🎯 Próximas Mejoras (Roadmap)

- [ ] Notificaciones por email automáticas
- [ ] Chat en tiempo real entre proveedores y técnicos
- [ ] Integración con SharePoint
- [ ] Reportes y analytics avanzados
- [ ] App móvil para consultas
- [ ] API REST para integraciones
- [ ] Inteligencia artificial para sugerencias

---

**Versión**: 1.0.0  
**Fecha**: Agosto 2024  
**Desarrollado por**: Equipo Técnico Indunnova