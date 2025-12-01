# Plan de Desarrollo - FASE 1 (MVP Urgente)
## Sistema de Gestión de Planes de Mejoramiento - Intercolombia
### Solución Rápida a Problemas Críticos

---

## RESUMEN EJECUTIVO FASE 1

### Objetivo Principal
Implementar en **6 semanas** una solución web mínima pero funcional que resuelva los problemas más críticos:
1. ✅ Eliminar la dependencia del formato rígido de correo
2. ✅ Dar transparencia inmediata del estado a los proveedores  
3. ✅ Reducir drásticamente los tiempos de gestión
4. ✅ Proveer trazabilidad completa del proceso

### Alcance Fase 1
**Lo que SÍ incluye:**
- Portal web básico pero funcional para proveedores
- Formulario inteligente para presentar planes
- Vista de estado en tiempo real
- Notificaciones automáticas por email
- Panel básico para técnicos
- Sincronización con SharePoint existente

**Lo que NO incluye (para fases posteriores):**
- Chat en tiempo real
- Inteligencia artificial
- App móvil
- Integraciones complejas con SAP
- Reportes avanzados

---

## 1. PROBLEMAS CRÍTICOS A RESOLVER INMEDIATAMENTE

### Prioridad 1: Eliminar el Formato Rígido de Correo
**Problema actual:**
```
❌ 40% de correos no procesados por errores de formato
❌ Proveedores frustrados sin saber si su mensaje fue recibido
❌ Sobrecarga manual para procesar correos mal formateados
```

**Solución Fase 1:**
```
✅ Formulario web intuitivo que elimina errores de formato
✅ Confirmación inmediata de recepción
✅ Validación en tiempo real de campos
```

### Prioridad 2: Transparencia del Proceso
**Problema actual:**
```
❌ Proveedores no saben el estado de su plan
❌ No hay visibilidad de plazos ni fechas límite
❌ Incertidumbre genera múltiples llamadas y correos
```

**Solución Fase 1:**
```
✅ Dashboard simple con estado actual visible 24/7
✅ Fechas límite claramente mostradas
✅ Historial de cambios y comentarios
```

### Prioridad 3: Reducción de Tiempos
**Problema actual:**
```
❌ 45 días promedio para aprobación
❌ Casos de más de 1 año sin resolver
❌ No hay alertas automáticas de vencimientos
```

**Solución Fase 1:**
```
✅ Notificaciones automáticas de vencimientos
✅ Escalamiento automático si no hay respuesta
✅ Dashboard para técnicos con planes pendientes
```

---

## 2. ARQUITECTURA TÉCNICA MÍNIMA FASE 1

### Stack Tecnológico Simplificado

```
Frontend (Simple pero Efectivo)
├── HTML5 + Bootstrap 5 (responsive)
├── JavaScript Vanilla / jQuery
├── Validación de formularios en cliente
└── AJAX para actualizaciones sin recargar

Backend (Django Robusto)
├── Django 5.0
├── PostgreSQL (Azure Database)
├── Django Templates (SSR)
└── Celery + Redis (notificaciones)

Infraestructura (Azure)
├── Azure App Service (Web App)
├── Azure Database for PostgreSQL
├── Azure Storage (documentos)
└── SendGrid (emails)
```

### Arquitectura Simplificada
```
┌─────────────────────────────────────┐
│     Portal Web (Django + Bootstrap) │
├─────────────────────────────────────┤
│  • Login Proveedores                │
│  • Formulario Planes                │
│  • Dashboard Estado                 │
│  • Panel Técnicos                   │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │   Django    │
        │   Backend   │
        └──────┬──────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
PostgreSQL   Redis    Blob Storage
    │                      
    └─── Sync cada 10 min ──→ SharePoint
```

---

## 3. FUNCIONALIDADES ESPECÍFICAS FASE 1

### 3.1 Portal de Proveedores (MVP)

#### A. Página de Login Simple
```html
<!-- Login minimalista pero seguro -->
┌────────────────────────────────────┐
│     GESTIÓN PLANES DE MEJORAMIENTO │
│            Intercolombia           │
├────────────────────────────────────┤
│                                    │
│  NIT: [___________]                │
│                                    │
│  Contraseña: [___________]         │
│                                    │
│  [✓] Recordarme                   │
│                                    │
│  [ INGRESAR ]                      │
│                                    │
│  ¿Olvidó su contraseña?            │
│  ¿Primera vez? Regístrese aquí     │
└────────────────────────────────────┘
```

#### B. Dashboard del Proveedor
```python
# Vista simplificada pero informativa
def dashboard_proveedor(request):
    proveedor = request.user.proveedor
    context = {
        'evaluacion_actual': {
            'puntaje': 72,
            'fecha': '2024-01-15',
            'estado_plan': 'EN_REVISION'
        },
        'notificaciones': [
            'Plan en revisión por técnico',
            'Plazo vence en 5 días'
        ],
        'progreso': {
            'enviado': True,
            'en_revision': True,
            'aprobado': False,
            'radicado': False
        }
    }
    return render(request, 'dashboard.html', context)
```

**Interfaz Dashboard:**
```
┌──────────────────────────────────────────┐
│  Bienvenido: PROVEEDOR XYZ LTDA         │
│  NIT: 900.123.456-7                     │
├──────────────────────────────────────────┤
│                                          │
│  EVALUACIÓN ACTUAL                      │
│  ┌────────────────────────────────────┐ │
│  │ Puntaje: 72/100 ⚠️                │ │
│  │ Fecha: 15/01/2024                  │ │
│  │ Requiere: Plan de Mejoramiento     │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ESTADO DE SU PLAN                      │
│  ┌────────────────────────────────────┐ │
│  │ ✅ Enviado:      15/01/2024        │ │
│  │ ⏳ En Revisión:  17/01/2024        │ │
│  │ ⏸️  Aprobado:     Pendiente         │ │
│  │ ⏸️  Radicado:     Pendiente         │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ⚠️ ATENCIÓN: Plazo vence en 5 días     │
│                                          │
│  [VER PLAN] [EDITAR] [DESCARGAR PDF]    │
└──────────────────────────────────────────┘
```

#### C. Formulario de Plan de Mejoramiento
```python
# forms.py - Formulario Django simple pero completo
class PlanMejoramientoForm(forms.ModelForm):
    class Meta:
        model = PlanMejoramiento
        fields = [
            'analisis_causa',
            'acciones_propuestas',
            'responsable',
            'fecha_implementacion',
            'indicadores_seguimiento',
            'documentos_soporte'
        ]
        widgets = {
            'analisis_causa': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describa las causas identificadas...',
                'class': 'form-control',
                'required': True
            }),
            'fecha_implementacion': forms.DateInput(attrs={
                'type': 'date',
                'min': date.today().isoformat(),
                'class': 'form-control'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        # Validaciones básicas pero importantes
        if len(cleaned_data.get('analisis_causa', '')) < 100:
            raise forms.ValidationError(
                "El análisis debe tener mínimo 100 caracteres"
            )
        return cleaned_data
```

**Interfaz del Formulario:**
```
┌──────────────────────────────────────────┐
│      CREAR PLAN DE MEJORAMIENTO          │
├──────────────────────────────────────────┤
│                                          │
│ 1. ANÁLISIS DE CAUSA RAÍZ *             │
│ ┌────────────────────────────────────┐  │
│ │ [Textarea - mínimo 100 caracteres] │  │
│ └────────────────────────────────────┘  │
│ ✓ 150/100 caracteres                    │
│                                          │
│ 2. ACCIONES DE MEJORA *                 │
│ ┌────────────────────────────────────┐  │
│ │ Acción 1: [___________________]    │  │
│ │ Responsable: [_________________]   │  │
│ │ Fecha: [📅 Seleccionar]           │  │
│ └────────────────────────────────────┘  │
│ [+ Agregar otra acción]                 │
│                                          │
│ 3. INDICADORES DE SEGUIMIENTO *         │
│ ┌────────────────────────────────────┐  │
│ │ [___________________________]      │  │
│ └────────────────────────────────────┘  │
│                                          │
│ 4. DOCUMENTOS DE SOPORTE                │
│ ┌────────────────────────────────────┐  │
│ │ 📎 Arrastrar archivos aquí         │  │
│ │    o hacer clic para seleccionar   │  │
│ └────────────────────────────────────┘  │
│                                          │
│ [GUARDAR BORRADOR] [ENVIAR PLAN]        │
└──────────────────────────────────────────┘
```

### 3.2 Panel de Técnicos (Básico)

#### Vista de Planes Pendientes
```python
# views.py - Panel técnico simplificado
@login_required
@user_passes_test(es_tecnico)
def panel_tecnico(request):
    planes_pendientes = PlanMejoramiento.objects.filter(
        estado='ESPERANDO_APROBACION'
    ).order_by('fecha_limite')
    
    context = {
        'planes_pendientes': planes_pendientes,
        'estadisticas': {
            'pendientes': planes_pendientes.count(),
            'vencidos': planes_pendientes.filter(
                fecha_limite__lt=date.today()
            ).count(),
            'proximos_vencer': planes_pendientes.filter(
                fecha_limite__lte=date.today() + timedelta(days=3)
            ).count()
        }
    }
    return render(request, 'panel_tecnico.html', context)
```

**Interfaz Panel Técnico:**
```
┌──────────────────────────────────────────┐
│        PANEL DE GESTIÓN - TÉCNICO        │
├──────────────────────────────────────────┤
│                                          │
│ RESUMEN                                  │
│ ┌─────────┬──────────┬────────────────┐ │
│ │ Pendientes │ Vencidos │ Por Vencer   │ │
│ │     12     │    3     │      5       │ │
│ └─────────┴──────────┴────────────────┘ │
│                                          │
│ PLANES PARA REVISAR                     │
│ ┌────────────────────────────────────┐  │
│ │ # │ Proveedor │ Fecha │ Estado     │  │
│ ├───┼───────────┼───────┼────────────┤  │
│ │ 1 │ ABC Ltda  │ 20/01 │ ⚠️ Vencido │  │
│ │ 2 │ XYZ SAS   │ 22/01 │ ⏰ 2 días  │  │
│ │ 3 │ 123 Corp  │ 25/01 │ ✓ A tiempo│  │
│ └────────────────────────────────────┘  │
│                                          │
│ [Clic en fila para revisar]             │
└──────────────────────────────────────────┘
```

#### Formulario de Revisión
```python
# Modelo simplificado de revisión
class RevisionPlan(models.Model):
    ESTADOS_REVISION = [
        ('APROBADO', 'Aprobado'),
        ('REQUIERE_AJUSTES', 'Requiere Ajustes'),
        ('RECHAZADO', 'Rechazado')
    ]
    
    plan = models.ForeignKey(PlanMejoramiento, on_delete=models.CASCADE)
    tecnico = models.ForeignKey(User, on_delete=models.CASCADE)
    estado_revision = models.CharField(max_length=20, choices=ESTADOS_REVISION)
    comentarios = models.TextField()
    fecha_revision = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Enviar notificación automática al proveedor
        enviar_notificacion_revision(self)
```

### 3.3 Sistema de Notificaciones Automáticas

```python
# tasks.py - Tareas Celery para notificaciones
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

@shared_task
def enviar_notificacion_nuevo_plan(plan_id):
    plan = PlanMejoramiento.objects.get(id=plan_id)
    
    # Para el proveedor - confirmación
    mensaje_proveedor = render_to_string('emails/plan_recibido.html', {
        'proveedor': plan.proveedor,
        'numero_radicado': plan.numero_radicado,
        'fecha_limite': plan.fecha_limite
    })
    
    send_mail(
        subject=f'Plan de Mejoramiento Recibido - Radicado {plan.numero_radicado}',
        message='',
        html_message=mensaje_proveedor,
        from_email='planes@intercolombia.com',
        recipient_list=[plan.proveedor.email]
    )
    
    # Para el técnico - nuevo plan para revisar
    tecnicos = User.objects.filter(groups__name='Tecnicos')
    for tecnico in tecnicos:
        send_mail(
            subject=f'Nuevo Plan para Revisión - {plan.proveedor.nombre}',
            message=f'Hay un nuevo plan de mejoramiento pendiente de revisión',
            from_email='planes@intercolombia.com',
            recipient_list=[tecnico.email]
        )

@shared_task
def verificar_vencimientos():
    """Ejecutar diariamente para alertar vencimientos"""
    from datetime import date, timedelta
    
    # Planes próximos a vencer (3 días)
    planes_por_vencer = PlanMejoramiento.objects.filter(
        estado='EN_PROCESO',
        fecha_limite__lte=date.today() + timedelta(days=3),
        fecha_limite__gte=date.today()
    )
    
    for plan in planes_por_vencer:
        dias_restantes = (plan.fecha_limite - date.today()).days
        
        send_mail(
            subject=f'⚠️ Plan de Mejoramiento vence en {dias_restantes} días',
            message=f'Su plan de mejoramiento vence el {plan.fecha_limite}',
            from_email='planes@intercolombia.com',
            recipient_list=[plan.proveedor.email]
        )

# Configurar en celery beat para ejecutar diariamente
CELERY_BEAT_SCHEDULE = {
    'verificar-vencimientos': {
        'task': 'planes.tasks.verificar_vencimientos',
        'schedule': crontab(hour=8, minute=0),  # 8 AM todos los días
    },
}
```

### 3.4 Sincronización con SharePoint

```python
# sync_sharepoint.py - Sincronización básica pero funcional
import requests
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

class SharePointSync:
    def __init__(self):
        self.site_url = "https://isaempresas.sharepoint.com/sites/SeguimientosDatosDA"
        self.username = settings.SHAREPOINT_USER
        self.password = settings.SHAREPOINT_PASS
        
    def sincronizar_evaluaciones(self):
        """Traer evaluaciones < 80 puntos desde SharePoint"""
        ctx = ClientContext(self.site_url).with_credentials(
            UserCredential(self.username, self.password)
        )
        
        # Obtener lista de evaluaciones
        lista = ctx.web.lists.get_by_title("Evaluaciones Proveedores")
        items = lista.items.filter("Puntaje lt 80").get().execute_query()
        
        for item in items:
            # Crear o actualizar en Django
            Evaluacion.objects.update_or_create(
                nit_proveedor=item.properties['NIT'],
                defaults={
                    'puntaje': item.properties['Puntaje'],
                    'fecha': item.properties['Fecha'],
                    'requiere_plan': True
                }
            )
    
    def enviar_actualizaciones_planes(self):
        """Enviar estados de planes a SharePoint"""
        planes_actualizados = PlanMejoramiento.objects.filter(
            sincronizado=False
        )
        
        for plan in planes_actualizados:
            # Actualizar en SharePoint
            self.actualizar_item_sharepoint(plan)
            plan.sincronizado = True
            plan.save()

# Tarea programada cada 10 minutos
@shared_task
def sincronizar_sharepoint():
    sync = SharePointSync()
    sync.sincronizar_evaluaciones()
    sync.enviar_actualizaciones_planes()
```

---

## 4. MODELOS DE DATOS ESENCIALES FASE 1

```python
# models.py - Modelos mínimos pero completos

class Proveedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nit = models.CharField(max_length=20, unique=True)
    razon_social = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nit} - {self.razon_social}"

class Evaluacion(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    periodo = models.CharField(max_length=50)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2)
    fecha = models.DateField()
    requiere_plan = models.BooleanField(default=False)
    documento_evaluacion = models.FileField(upload_to='evaluaciones/')
    
    class Meta:
        unique_together = ['proveedor', 'periodo']
    
    def save(self, *args, **kwargs):
        if self.puntaje < 80:
            self.requiere_plan = True
        super().save(*args, **kwargs)

class PlanMejoramiento(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('ENVIADO', 'Enviado'),
        ('EN_REVISION', 'En Revisión'),
        ('REQUIERE_AJUSTES', 'Requiere Ajustes'),
        ('APROBADO', 'Aprobado'),
        ('RADICADO', 'Radicado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    numero_radicado = models.CharField(max_length=50, unique=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    
    # Campos del plan
    analisis_causa = models.TextField()
    acciones_propuestas = models.TextField()
    responsable = models.CharField(max_length=200)
    fecha_implementacion = models.DateField()
    indicadores_seguimiento = models.TextField()
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    
    # Sincronización
    sincronizado_sharepoint = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.numero_radicado and self.estado == 'ENVIADO':
            self.numero_radicado = self.generar_numero_radicado()
        super().save(*args, **kwargs)
    
    def generar_numero_radicado(self):
        from datetime import datetime
        return f"PM-{datetime.now().strftime('%Y%m%d%H%M%S')}"

class DocumentoPlan(models.Model):
    plan = models.ForeignKey(PlanMejoramiento, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='planes/documentos/')
    nombre = models.CharField(max_length=200)
    fecha_carga = models.DateTimeField(auto_now_add=True)

class HistorialPlan(models.Model):
    plan = models.ForeignKey(PlanMejoramiento, on_delete=models.CASCADE)
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    comentario = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
```

---

## 5. CRONOGRAMA DETALLADO - 6 SEMANAS

### Semana 1: Configuración y Base
```
Día 1-2: Configuración del Proyecto
├── Configurar Azure (App Service, DB, Storage)
├── Crear proyecto Django
├── Configurar PostgreSQL
└── Estructura básica de carpetas

Día 3-4: Modelos y Migraciones
├── Crear modelos de datos
├── Configurar admin Django
├── Migraciones iniciales
└── Fixtures de datos de prueba

Día 5: Autenticación
├── Sistema de login/logout
├── Registro de proveedores
├── Recuperación de contraseña
└── Decoradores de permisos
```

### Semana 2: Portal de Proveedores
```
Día 1-2: Dashboard Proveedor
├── Vista principal dashboard
├── Mostrar evaluación actual
├── Estado del plan
└── Notificaciones pendientes

Día 3-4: Formulario de Plan
├── Crear formulario Django
├── Validaciones en cliente
├── Guardado de borradores
└── Carga de archivos

Día 5: Flujo de Estados
├── Lógica de transición de estados
├── Historial de cambios
├── Permisos por estado
└── Tests unitarios
```

### Semana 3: Panel de Técnicos
```
Día 1-2: Dashboard Técnico
├── Vista de planes pendientes
├── Filtros y búsqueda
├── Estadísticas básicas
└── Alertas de vencimientos

Día 3-4: Revisión de Planes
├── Vista detalle del plan
├── Formulario de revisión
├── Aprobación/Rechazo
└── Solicitud de ajustes

Día 5: Reportes Básicos
├── Listado de planes
├── Exportar a Excel
├── Vista de impresión
└── Gráficos simples
```

### Semana 4: Notificaciones y Sincronización
```
Día 1-2: Sistema de Notificaciones
├── Configurar Celery + Redis
├── Templates de email
├── Notificaciones de estado
└── Recordatorios automáticos

Día 3-4: Sincronización SharePoint
├── Conexión con SharePoint
├── Importar evaluaciones
├── Exportar estados de planes
└── Logs de sincronización

Día 5: Optimización
├── Caché de consultas frecuentes
├── Índices en base de datos
├── Compresión de assets
└── Lazy loading de imágenes
```

### Semana 5: Testing y Ajustes
```
Día 1-2: Testing Funcional
├── Tests de formularios
├── Tests de flujos completos
├── Tests de permisos
└── Tests de notificaciones

Día 3-4: Testing con Usuarios
├── 5 proveedores piloto
├── 2 técnicos de prueba
├── Recolección de feedback
└── Ajustes urgentes

Día 5: Correcciones
├── Fix de bugs críticos
├── Ajustes de UI/UX
├── Mejoras de performance
└── Documentación básica
```

### Semana 6: Despliegue y Capacitación
```
Día 1-2: Preparación Producción
├── Configuración SSL
├── Dominios y DNS
├── Backups automáticos
└── Monitoreo básico

Día 3: Migración de Datos
├── Importar proveedores
├── Importar evaluaciones históricas
├── Verificación de integridad
└── Rollback plan

Día 4: Capacitación
├── Manual de usuario (PDF)
├── Videos tutoriales (3-5 min)
├── Sesión con técnicos (2h)
├── Sesión con proveedores piloto (2h)

Día 5: Go-Live
├── Despliegue a producción
├── Monitoreo intensivo
├── Soporte en sitio
└── Ajustes en caliente
```

---

## 6. ESTRUCTURA DE PROYECTO FASE 1

```
planes-mejoramiento-mvp/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
│
├── apps/
│   ├── usuarios/
│   │   ├── models.py         # Proveedor, perfiles
│   │   ├── views.py          # Login, registro
│   │   ├── forms.py          # Formularios auth
│   │   └── templates/
│   │       ├── login.html
│   │       └── registro.html
│   │
│   ├── planes/
│   │   ├── models.py         # PlanMejoramiento, Evaluacion
│   │   ├── views.py          # CRUD planes
│   │   ├── forms.py          # Formulario plan
│   │   ├── tasks.py          # Tareas Celery
│   │   └── templates/
│   │       ├── dashboard.html
│   │       ├── plan_form.html
│   │       └── plan_detail.html
│   │
│   ├── tecnicos/
│   │   ├── views.py          # Panel técnico
│   │   ├── forms.py          # Form revisión
│   │   └── templates/
│   │       ├── panel.html
│   │       └── revisar_plan.html
│   │
│   └── sincronizacion/
│       ├── sharepoint.py     # Cliente SharePoint
│       ├── tasks.py          # Sync automático
│       └── management/
│           └── commands/
│               └── sync_sharepoint.py
│
├── static/
│   ├── css/
│   │   ├── bootstrap.min.css
│   │   └── custom.css
│   ├── js/
│   │   ├── jquery.min.js
│   │   ├── bootstrap.bundle.min.js
│   │   └── app.js
│   └── img/
│       └── logo.png
│
├── media/
│   ├── evaluaciones/
│   └── planes/
│
├── templates/
│   ├── base.html
│   ├── navbar.html
│   └── emails/
│       ├── plan_recibido.html
│       ├── plan_aprobado.html
│       └── recordatorio.html
│
└── docker/
    ├── Dockerfile
    ├── docker-compose.yml
    └── entrypoint.sh
```

---

## 7. CONFIGURACIÓN RÁPIDA AZURE

### Script de Despliegue Automático
```bash
#!/bin/bash
# deploy_azure.sh

# Variables
RESOURCE_GROUP="rg-planes-mejoramiento"
LOCATION="eastus2"
APP_NAME="planes-intercolombia"
DB_SERVER="planes-db-server"
DB_NAME="planesdb"

# Crear Resource Group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Crear PostgreSQL
az postgres server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER \
  --location $LOCATION \
  --admin-user adminuser \
  --admin-password SecurePass123! \
  --sku-name B_Gen5_1

# Crear App Service Plan
az appservice plan create \
  --name "${APP_NAME}-plan" \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# Crear Web App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan "${APP_NAME}-plan" \
  --name $APP_NAME \
  --runtime "PYTHON|3.11"

# Configurar variables de entorno
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    DATABASE_URL="postgresql://adminuser:SecurePass123!@${DB_SERVER}.postgres.database.azure.com/${DB_NAME}" \
    SECRET_KEY="django-insecure-change-this-in-production" \
    DEBUG="False" \
    ALLOWED_HOSTS="${APP_NAME}.azurewebsites.net"

# Deploy desde GitHub
az webapp deployment source config \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --repo-url https://github.com/intercolombia/planes-mejoramiento \
  --branch main \
  --manual-integration

echo "Despliegue completado! URL: https://${APP_NAME}.azurewebsites.net"
```

---

## 8. MÉTRICAS DE ÉXITO FASE 1

### KPIs Inmediatos (Primera Semana Post-Launch)
- ✅ 100% de planes recibidos correctamente (vs 60% actual)
- ✅ 0 errores por formato de correo
- ✅ 90% de proveedores pueden ver su estado
- ✅ Reducción 50% en llamadas preguntando por estado

### KPIs a 30 Días
- ✅ Tiempo promedio de aprobación < 15 días (vs 45 actual)
- ✅ 80% de satisfacción en encuesta a proveedores
- ✅ 100% de trazabilidad en el proceso
- ✅ 0 planes perdidos o sin procesar

### KPIs a 60 Días
- ✅ ROI positivo por ahorro en horas administrativas
- ✅ 95% de planes presentados a tiempo
- ✅ Reducción 70% en reprocesos
- ✅ NPS > 7 de proveedores con el nuevo sistema

---

## 9. RIESGOS Y MITIGACIONES FASE 1

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Resistencia de proveedores al cambio | Media | Alto | Capacitación intensiva, soporte 24/7 primera semana |
| Problemas de sincronización con SharePoint | Media | Medio | Sincronización manual como backup, logs detallados |
| Bugs en producción | Baja | Alto | Testing exhaustivo, rollback plan, hotfix process |
| Sobrecarga del sistema | Baja | Medio | Auto-scaling en Azure, caché agresivo |
| Problemas de login proveedores | Media | Alto | Múltiples métodos de recuperación, soporte telefónico |

---

## 10. COSTOS FASE 1

### Desarrollo (6 semanas)
```
1 Desarrollador Senior Full Stack: $24,000,000 COP
1 Desarrollador Junior (soporte):  $12,000,000 COP
0.5 Diseñador UI (3 semanas):      $6,000,000 COP
Project Manager (20%):              $4,800,000 COP
-------------------------------------------
Subtotal Desarrollo:                $46,800,000 COP
```

### Infraestructura (Primer Año)
```
Azure App Service (B2):             $1,200,000 COP/mes
PostgreSQL Database:                $800,000 COP/mes
Storage + Backup:                   $200,000 COP/mes
SendGrid (emails):                  $100,000 COP/mes
-------------------------------------------
Subtotal Mensual:                   $2,300,000 COP
Subtotal Anual:                     $27,600,000 COP
```

### Total Fase 1
```
Desarrollo:                         $46,800,000 COP
Infraestructura Año 1:              $27,600,000 COP
Contingencia (10%):                 $7,440,000 COP
-------------------------------------------
TOTAL FASE 1:                       $81,840,000 COP
```

**ROI Esperado:**
- Ahorro mensual estimado: $12,500,000 COP
- Recuperación inversión: 6.5 meses
- ROI primer año: 53%

---

## CONCLUSIÓN

Esta Fase 1 está diseñada para resolver los problemas más críticos y urgentes del sistema actual en solo 6 semanas, con una inversión mínima pero retorno máximo. 

**Beneficios Inmediatos:**
1. ✅ Elimina completamente el problema del formato de correo
2. ✅ Da transparencia total a los proveedores
3. ✅ Reduce tiempos de gestión en 70%
4. ✅ Provee base sólida para futuras mejoras

**Próximos Pasos Inmediatos:**
1. Aprobación del plan (1 día)
2. Formación del equipo (2 días)
3. Inicio del desarrollo (Día 4)

Con esta solución MVP, Intercolombia puede resolver sus problemas más urgentes rápidamente, mientras construye la base para el sistema completo en fases posteriores.