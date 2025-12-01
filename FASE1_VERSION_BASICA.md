# Plan de Desarrollo - FASE 1 VERSIÓN BÁSICA
## Sistema Web de Planes de Mejoramiento - Sin IA ni Notificaciones
### Solución Mínima Viable - Solo Interacción Web

---

## RESUMEN EJECUTIVO

### Objetivo
Implementar en **4 semanas** una plataforma web básica que resuelva el problema principal:
- ✅ **Eliminar el formato rígido de correo** 
- ✅ **Portal web donde proveedores presentan planes directamente**
- ✅ **Panel para técnicos para revisar y aprobar**
- ✅ **Transparencia del estado del proceso**

### Lo que SÍ incluye
- Portal web funcional
- Login para proveedores y técnicos
- Formulario web para crear planes
- Panel de revisión para técnicos
- Estados visibles del proceso
- Carga y descarga de documentos

### Lo que NO incluye en esta versión
- ❌ Inteligencia artificial
- ❌ Notificaciones por email/SMS
- ❌ Chat en tiempo real
- ❌ Análisis predictivo
- ❌ Integraciones con SharePoint
- ❌ Validaciones automáticas complejas

---

## 1. ARQUITECTURA TÉCNICA SIMPLIFICADA

### Stack Mínimo
```
Backend:
- Django 5.0
- PostgreSQL
- Python 3.11

Frontend:
- HTML5 + CSS3
- Bootstrap 5
- JavaScript básico
- Django Templates

Servidor:
- Gunicorn
- Nginx
- Ubuntu Server
```

### Estructura Simple
```
┌─────────────────────────┐
│   Navegador Web         │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   Django Web Server     │
│   - Views               │
│   - Forms               │
│   - Templates           │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   PostgreSQL DB         │
└─────────────────────────┘
```

---

## 2. FLUJOS DE INTERACCIÓN BÁSICOS

### 2.1 Flujo del Proveedor

```
1. ACCESO AL SISTEMA
   └── Proveedor ingresa URL en navegador
   └── Ve página de login
   └── Ingresa NIT y contraseña
   └── Accede a su dashboard

2. VER SU SITUACIÓN
   └── Ve su evaluación actual
   └── Ve si necesita presentar plan
   └── Ve fecha límite

3. CREAR PLAN
   └── Clic en "Crear Plan"
   └── Llena formulario web
   └── Adjunta documentos
   └── Clic en "Enviar"

4. SEGUIMIENTO
   └── Ingresa cuando quiera
   └── Ve estado actual
   └── Ve comentarios del técnico
   └── Puede responder a solicitudes
```

### 2.2 Flujo del Técnico

```
1. ACCESO AL SISTEMA
   └── Técnico ingresa URL
   └── Login con usuario/contraseña
   └── Ve panel con planes pendientes

2. REVISAR PLAN
   └── Clic en plan pendiente
   └── Lee el contenido
   └── Descarga documentos adjuntos
   └── Escribe comentarios

3. TOMAR DECISIÓN
   └── Selecciona: Aprobar/Ajustes/Rechazar
   └── Escribe justificación
   └── Clic en "Guardar"
   └── Sistema actualiza estado
```

---

## 3. INTERFACES DE USUARIO SIMPLIFICADAS

### 3.1 Login (Único para todos)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Sistema Planes de Mejoramiento</title>
    <link href="bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h4>Ingreso al Sistema</h4>
                    </div>
                    <div class="card-body">
                        <form method="POST">
                            {% csrf_token %}
                            <div class="mb-3">
                                <label>Usuario (NIT):</label>
                                <input type="text" name="username" 
                                       class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>Contraseña:</label>
                                <input type="password" name="password" 
                                       class="form-control" required>
                            </div>
                            <button type="submit" 
                                    class="btn btn-primary w-100">
                                Ingresar
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
```

### 3.2 Dashboard Proveedor (Simple)

```html
<!-- dashboard_proveedor.html -->
<div class="container mt-4">
    <h2>Bienvenido {{ proveedor.razon_social }}</h2>
    
    <!-- Información de Evaluación -->
    <div class="card mb-4">
        <div class="card-header bg-warning text-dark">
            <h5>Evaluación Actual</h5>
        </div>
        <div class="card-body">
            <p><strong>Período:</strong> {{ evaluacion.periodo }}</p>
            <p><strong>Puntaje:</strong> {{ evaluacion.puntaje }}/100</p>
            <p><strong>Estado:</strong> Requiere Plan de Mejoramiento</p>
            <p><strong>Fecha Límite:</strong> {{ fecha_limite }}</p>
        </div>
    </div>
    
    <!-- Estado del Plan -->
    {% if plan_actual %}
    <div class="card mb-4">
        <div class="card-header">
            <h5>Estado de su Plan</h5>
        </div>
        <div class="card-body">
            <p><strong>Estado:</strong> 
                <span class="badge bg-info">{{ plan_actual.get_estado_display }}</span>
            </p>
            <p><strong>Fecha Envío:</strong> {{ plan_actual.fecha_envio }}</p>
            
            {% if plan_actual.comentarios_tecnico %}
            <div class="alert alert-info">
                <strong>Comentarios del Técnico:</strong><br>
                {{ plan_actual.comentarios_tecnico }}
            </div>
            {% endif %}
            
            <a href="{% url 'ver_plan' plan_actual.id %}" 
               class="btn btn-primary">Ver Plan</a>
            
            {% if plan_actual.estado == 'REQUIERE_AJUSTES' %}
            <a href="{% url 'editar_plan' plan_actual.id %}" 
               class="btn btn-warning">Realizar Ajustes</a>
            {% endif %}
        </div>
    </div>
    {% else %}
    <!-- Crear Nuevo Plan -->
    <div class="card">
        <div class="card-body text-center">
            <p>No ha presentado un plan de mejoramiento</p>
            <a href="{% url 'crear_plan' %}" 
               class="btn btn-success btn-lg">
                Crear Plan de Mejoramiento
            </a>
        </div>
    </div>
    {% endif %}
</div>
```

### 3.3 Formulario de Plan (Básico)

```html
<!-- crear_plan.html -->
<div class="container mt-4">
    <h3>Crear Plan de Mejoramiento</h3>
    
    <form method="POST" enctype="multipart/form-data">
        {% csrf_token %}
        
        <div class="card mb-3">
            <div class="card-header">
                <h5>1. Análisis de Causa Raíz</h5>
            </div>
            <div class="card-body">
                <textarea name="analisis_causa" 
                          class="form-control" 
                          rows="5" 
                          required
                          placeholder="Explique las causas de los problemas identificados">
                </textarea>
            </div>
        </div>
        
        <div class="card mb-3">
            <div class="card-header">
                <h5>2. Acciones de Mejora</h5>
            </div>
            <div class="card-body">
                <div id="acciones-container">
                    <div class="accion-item mb-3">
                        <input type="text" 
                               name="accion_1" 
                               class="form-control mb-2" 
                               placeholder="Descripción de la acción"
                               required>
                        <input type="text" 
                               name="responsable_1" 
                               class="form-control mb-2" 
                               placeholder="Responsable">
                        <input type="date" 
                               name="fecha_1" 
                               class="form-control"
                               required>
                    </div>
                </div>
                <button type="button" 
                        onclick="agregarAccion()" 
                        class="btn btn-sm btn-secondary">
                    + Agregar Acción
                </button>
            </div>
        </div>
        
        <div class="card mb-3">
            <div class="card-header">
                <h5>3. Indicadores de Seguimiento</h5>
            </div>
            <div class="card-body">
                <textarea name="indicadores" 
                          class="form-control" 
                          rows="3"
                          required
                          placeholder="Describa cómo medirá el éxito">
                </textarea>
            </div>
        </div>
        
        <div class="card mb-3">
            <div class="card-header">
                <h5>4. Documentos de Soporte (Opcional)</h5>
            </div>
            <div class="card-body">
                <input type="file" 
                       name="documentos" 
                       class="form-control" 
                       multiple>
                <small class="text-muted">
                    Formatos: PDF, DOC, XLS. Máximo 10MB por archivo
                </small>
            </div>
        </div>
        
        <div class="d-flex justify-content-between">
            <a href="{% url 'dashboard' %}" 
               class="btn btn-secondary">Cancelar</a>
            <button type="submit" 
                    class="btn btn-primary btn-lg">
                Enviar Plan
            </button>
        </div>
    </form>
</div>

<script>
let contadorAcciones = 1;

function agregarAccion() {
    contadorAcciones++;
    const container = document.getElementById('acciones-container');
    const div = document.createElement('div');
    div.className = 'accion-item mb-3';
    div.innerHTML = `
        <input type="text" name="accion_${contadorAcciones}" 
               class="form-control mb-2" 
               placeholder="Descripción de la acción">
        <input type="text" name="responsable_${contadorAcciones}" 
               class="form-control mb-2" 
               placeholder="Responsable">
        <input type="date" name="fecha_${contadorAcciones}" 
               class="form-control">
    `;
    container.appendChild(div);
}
</script>
```

### 3.4 Panel del Técnico (Simple)

```html
<!-- panel_tecnico.html -->
<div class="container-fluid mt-4">
    <h3>Panel de Revisión - Técnico</h3>
    
    <!-- Resumen -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5>{{ pendientes_count }}</h5>
                    <p>Pendientes</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5>{{ revision_count }}</h5>
                    <p>En Revisión</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5>{{ aprobados_count }}</h5>
                    <p>Aprobados</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5>{{ vencidos_count }}</h5>
                    <p class="text-danger">Vencidos</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Lista de Planes -->
    <div class="card">
        <div class="card-header">
            <h5>Planes para Revisar</h5>
        </div>
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>Proveedor</th>
                        <th>NIT</th>
                        <th>Puntaje</th>
                        <th>Fecha Envío</th>
                        <th>Estado</th>
                        <th>Días Pendiente</th>
                        <th>Acción</th>
                    </tr>
                </thead>
                <tbody>
                    {% for plan in planes %}
                    <tr>
                        <td>{{ plan.proveedor.razon_social }}</td>
                        <td>{{ plan.proveedor.nit }}</td>
                        <td>{{ plan.evaluacion.puntaje }}/100</td>
                        <td>{{ plan.fecha_envio|date:"d/m/Y" }}</td>
                        <td>
                            <span class="badge bg-warning">
                                {{ plan.get_estado_display }}
                            </span>
                        </td>
                        <td>
                            {% if plan.dias_pendiente > 5 %}
                                <span class="text-danger">
                                    {{ plan.dias_pendiente }} días
                                </span>
                            {% else %}
                                {{ plan.dias_pendiente }} días
                            {% endif %}
                        </td>
                        <td>
                            <a href="{% url 'revisar_plan' plan.id %}" 
                               class="btn btn-sm btn-primary">
                                Revisar
                            </a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
```

### 3.5 Vista de Revisión del Plan

```html
<!-- revisar_plan.html -->
<div class="container mt-4">
    <h3>Revisar Plan de Mejoramiento</h3>
    
    <!-- Información del Proveedor -->
    <div class="card mb-3">
        <div class="card-header">
            <h5>Información del Proveedor</h5>
        </div>
        <div class="card-body">
            <p><strong>Empresa:</strong> {{ plan.proveedor.razon_social }}</p>
            <p><strong>NIT:</strong> {{ plan.proveedor.nit }}</p>
            <p><strong>Evaluación:</strong> {{ plan.evaluacion.puntaje }}/100</p>
            <p><strong>Fecha Envío:</strong> {{ plan.fecha_envio }}</p>
        </div>
    </div>
    
    <!-- Contenido del Plan -->
    <div class="card mb-3">
        <div class="card-header">
            <h5>Plan Presentado</h5>
        </div>
        <div class="card-body">
            <h6>Análisis de Causa Raíz:</h6>
            <p class="border p-2">{{ plan.analisis_causa }}</p>
            
            <h6>Acciones de Mejora:</h6>
            <p class="border p-2">{{ plan.acciones_propuestas }}</p>
            
            <h6>Responsable:</h6>
            <p>{{ plan.responsable }}</p>
            
            <h6>Fecha de Implementación:</h6>
            <p>{{ plan.fecha_implementacion }}</p>
            
            <h6>Indicadores:</h6>
            <p class="border p-2">{{ plan.indicadores_seguimiento }}</p>
            
            {% if plan.documentos.all %}
            <h6>Documentos Adjuntos:</h6>
            <ul>
                {% for doc in plan.documentos.all %}
                <li>
                    <a href="{{ doc.archivo.url }}" target="_blank">
                        {{ doc.nombre }}
                    </a>
                </li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>
    
    <!-- Formulario de Revisión -->
    <div class="card mb-3">
        <div class="card-header">
            <h5>Mi Revisión</h5>
        </div>
        <div class="card-body">
            <form method="POST">
                {% csrf_token %}
                
                <div class="mb-3">
                    <label>Decisión:</label>
                    <select name="decision" class="form-select" required>
                        <option value="">Seleccione...</option>
                        <option value="APROBADO">Aprobar</option>
                        <option value="REQUIERE_AJUSTES">Solicitar Ajustes</option>
                        <option value="RECHAZADO">Rechazar</option>
                    </select>
                </div>
                
                <div class="mb-3">
                    <label>Comentarios para el Proveedor:</label>
                    <textarea name="comentarios" 
                              class="form-control" 
                              rows="5"
                              required
                              placeholder="Escriba sus observaciones...">
                    </textarea>
                </div>
                
                <div class="d-flex justify-content-between">
                    <a href="{% url 'panel_tecnico' %}" 
                       class="btn btn-secondary">
                        Volver
                    </a>
                    <button type="submit" class="btn btn-primary">
                        Guardar Revisión
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
```

---

## 4. MODELOS DE DATOS BÁSICOS

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta

class Proveedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nit = models.CharField(max_length=20, unique=True)
    razon_social = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.nit} - {self.razon_social}"

class Evaluacion(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    periodo = models.CharField(max_length=50)
    puntaje = models.IntegerField()
    fecha = models.DateField()
    
    def requiere_plan(self):
        return self.puntaje < 80

class PlanMejoramiento(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('ENVIADO', 'Enviado'),
        ('EN_REVISION', 'En Revisión'),
        ('REQUIERE_AJUSTES', 'Requiere Ajustes'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    
    # Contenido del plan
    analisis_causa = models.TextField()
    acciones_propuestas = models.TextField()
    responsable = models.CharField(max_length=200)
    fecha_implementacion = models.DateField()
    indicadores_seguimiento = models.TextField()
    
    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    
    # Revisión del técnico
    comentarios_tecnico = models.TextField(blank=True)
    fecha_revision = models.DateTimeField(null=True, blank=True)
    revisado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='planes_revisados'
    )
    
    def save(self, *args, **kwargs):
        if not self.fecha_limite:
            self.fecha_limite = date.today() + timedelta(days=20)
        super().save(*args, **kwargs)
    
    @property
    def dias_pendiente(self):
        if self.fecha_envio:
            return (date.today() - self.fecha_envio.date()).days
        return 0

class DocumentoPlan(models.Model):
    plan = models.ForeignKey(
        PlanMejoramiento, 
        on_delete=models.CASCADE,
        related_name='documentos'
    )
    archivo = models.FileField(upload_to='planes/')
    nombre = models.CharField(max_length=200)
    fecha_carga = models.DateTimeField(auto_now_add=True)
```

---

## 5. VISTAS BÁSICAS (VIEWS)

```python
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.utils import timezone
from .models import *
from .forms import PlanMejoramientoForm

# Vista de Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if hasattr(user, 'proveedor'):
                return redirect('dashboard_proveedor')
            else:
                return redirect('panel_tecnico')
    return render(request, 'login.html')

# Dashboard del Proveedor
@login_required
def dashboard_proveedor(request):
    proveedor = request.user.proveedor
    evaluacion = Evaluacion.objects.filter(
        proveedor=proveedor
    ).order_by('-fecha').first()
    
    plan_actual = PlanMejoramiento.objects.filter(
        proveedor=proveedor,
        evaluacion=evaluacion
    ).first()
    
    context = {
        'proveedor': proveedor,
        'evaluacion': evaluacion,
        'plan_actual': plan_actual,
        'fecha_limite': plan_actual.fecha_limite if plan_actual else None
    }
    return render(request, 'dashboard_proveedor.html', context)

# Crear Plan
@login_required
def crear_plan(request):
    proveedor = request.user.proveedor
    evaluacion = Evaluacion.objects.filter(
        proveedor=proveedor
    ).order_by('-fecha').first()
    
    if request.method == 'POST':
        plan = PlanMejoramiento.objects.create(
            evaluacion=evaluacion,
            proveedor=proveedor,
            analisis_causa=request.POST['analisis_causa'],
            acciones_propuestas=request.POST.get('acciones', ''),
            responsable=request.POST.get('responsable', ''),
            fecha_implementacion=request.POST['fecha_implementacion'],
            indicadores_seguimiento=request.POST['indicadores'],
            estado='ENVIADO',
            fecha_envio=timezone.now()
        )
        
        # Guardar documentos si hay
        for archivo in request.FILES.getlist('documentos'):
            DocumentoPlan.objects.create(
                plan=plan,
                archivo=archivo,
                nombre=archivo.name
            )
        
        return redirect('dashboard_proveedor')
    
    return render(request, 'crear_plan.html', {'evaluacion': evaluacion})

# Panel del Técnico
@login_required
def panel_tecnico(request):
    planes = PlanMejoramiento.objects.filter(
        estado__in=['ENVIADO', 'EN_REVISION']
    ).order_by('fecha_envio')
    
    context = {
        'planes': planes,
        'pendientes_count': planes.filter(estado='ENVIADO').count(),
        'revision_count': planes.filter(estado='EN_REVISION').count(),
        'aprobados_count': PlanMejoramiento.objects.filter(
            estado='APROBADO'
        ).count(),
        'vencidos_count': planes.filter(
            fecha_limite__lt=date.today()
        ).count()
    }
    return render(request, 'panel_tecnico.html', context)

# Revisar Plan
@login_required
def revisar_plan(request, plan_id):
    plan = get_object_or_404(PlanMejoramiento, id=plan_id)
    
    if request.method == 'POST':
        decision = request.POST['decision']
        comentarios = request.POST['comentarios']
        
        plan.estado = decision
        plan.comentarios_tecnico = comentarios
        plan.fecha_revision = timezone.now()
        plan.revisado_por = request.user
        plan.save()
        
        return redirect('panel_tecnico')
    
    return render(request, 'revisar_plan.html', {'plan': plan})

# Ver Plan (para proveedor)
@login_required
def ver_plan(request, plan_id):
    plan = get_object_or_404(
        PlanMejoramiento, 
        id=plan_id,
        proveedor=request.user.proveedor
    )
    return render(request, 'ver_plan.html', {'plan': plan})

# Editar Plan (cuando requiere ajustes)
@login_required
def editar_plan(request, plan_id):
    plan = get_object_or_404(
        PlanMejoramiento,
        id=plan_id,
        proveedor=request.user.proveedor,
        estado='REQUIERE_AJUSTES'
    )
    
    if request.method == 'POST':
        plan.analisis_causa = request.POST['analisis_causa']
        plan.acciones_propuestas = request.POST['acciones']
        plan.responsable = request.POST['responsable']
        plan.fecha_implementacion = request.POST['fecha_implementacion']
        plan.indicadores_seguimiento = request.POST['indicadores']
        plan.estado = 'ENVIADO'
        plan.fecha_envio = timezone.now()
        plan.save()
        
        return redirect('dashboard_proveedor')
    
    return render(request, 'editar_plan.html', {'plan': plan})
```

---

## 6. URLs BÁSICAS

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Login
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    
    # Proveedor
    path('dashboard/', views.dashboard_proveedor, name='dashboard_proveedor'),
    path('plan/crear/', views.crear_plan, name='crear_plan'),
    path('plan/<int:plan_id>/', views.ver_plan, name='ver_plan'),
    path('plan/<int:plan_id>/editar/', views.editar_plan, name='editar_plan'),
    
    # Técnico
    path('tecnico/', views.panel_tecnico, name='panel_tecnico'),
    path('tecnico/revisar/<int:plan_id>/', views.revisar_plan, name='revisar_plan'),
]
```

---

## 7. CONFIGURACIÓN BÁSICA

```python
# settings.py (fragmento)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'planes',  # nuestra app
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'planes_mejoramiento',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
```

---

## 8. CRONOGRAMA SIMPLIFICADO - 4 SEMANAS

### Semana 1: Base
```
Día 1-2: Configuración
- Instalar Django y PostgreSQL
- Crear proyecto y app
- Configurar settings

Día 3-4: Modelos y Admin
- Crear modelos de datos
- Configurar Django Admin
- Crear superusuario

Día 5: Autenticación
- Sistema de login
- Crear usuarios de prueba
```

### Semana 2: Portal Proveedor
```
Día 1-2: Dashboard
- Vista dashboard proveedor
- Mostrar evaluación y estado

Día 3-4: Formulario Plan
- Crear formulario
- Guardar en base de datos

Día 5: Carga de Archivos
- Configurar media files
- Upload de documentos
```

### Semana 3: Panel Técnico
```
Día 1-2: Panel Principal
- Vista de planes pendientes
- Contadores y estadísticas

Día 3-4: Revisión
- Vista detalle del plan
- Formulario de decisión

Día 5: Estados
- Lógica de cambio de estados
- Actualización de comentarios
```

### Semana 4: Testing y Deploy
```
Día 1-2: Testing
- Pruebas funcionales
- Corrección de bugs

Día 3: Datos de Prueba
- Cargar proveedores
- Crear evaluaciones ejemplo

Día 4-5: Despliegue
- Configurar servidor
- Deploy en producción
```

---

## 9. COMANDOS DE INSTALACIÓN

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Instalar dependencias
pip install django==5.0
pip install psycopg2-binary
pip install pillow  # para manejo de archivos

# 3. Crear proyecto
django-admin startproject config .
python manage.py startapp planes

# 4. Migraciones
python manage.py makemigrations
python manage.py migrate

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Correr servidor
python manage.py runserver
```

---

## 10. ESTRUCTURA DE ARCHIVOS FINAL

```
planes-mejoramiento-basico/
├── manage.py
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── planes/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard_proveedor.html
│   │   ├── crear_plan.html
│   │   ├── ver_plan.html
│   │   ├── editar_plan.html
│   │   ├── panel_tecnico.html
│   │   └── revisar_plan.html
│   └── static/
│       ├── css/
│       │   └── bootstrap.min.css
│       └── js/
│           └── bootstrap.bundle.min.js
└── media/
    └── planes/
```

---

## 11. DATOS DE PRUEBA

```python
# crear_datos_prueba.py
from django.contrib.auth.models import User
from planes.models import *
from datetime import date

# Crear técnico
tecnico_user = User.objects.create_user(
    username='tecnico1',
    password='pass123',
    first_name='Carlos',
    last_name='Mendoza'
)

# Crear proveedores
for i in range(1, 4):
    user = User.objects.create_user(
        username=f'90012345{i}',
        password='pass123'
    )
    
    proveedor = Proveedor.objects.create(
        user=user,
        nit=f'900.123.45{i}-7',
        razon_social=f'Proveedor {i} SAS',
        email=f'proveedor{i}@email.com',
        telefono='3001234567'
    )
    
    # Crear evaluación
    evaluacion = Evaluacion.objects.create(
        proveedor=proveedor,
        periodo='2024-Q1',
        puntaje=65 + i*5,  # 70, 75, 80
        fecha=date.today()
    )

print("Datos de prueba creados")
print("Usuario técnico: tecnico1 / pass123")
print("Proveedores: 900123451 / pass123")
```

---

## 12. RESULTADO ESPERADO

### Lo que el sistema hace:

1. **Proveedor ingresa con NIT y contraseña**
   - Ve su evaluación
   - Ve si necesita plan
   - Puede crear y enviar plan

2. **Técnico ingresa con usuario y contraseña**
   - Ve todos los planes pendientes
   - Puede revisar cada uno
   - Puede aprobar o pedir ajustes

3. **El sistema actualiza estados**
   - Cuando proveedor envía: ENVIADO
   - Cuando técnico revisa: APROBADO/REQUIERE_AJUSTES/RECHAZADO
   - Proveedor puede ver el estado actual

### Lo que NO hace esta versión:
- No envía emails
- No tiene chat
- No tiene IA
- No valida automáticamente
- No se integra con SharePoint
- No tiene notificaciones push

---

## CONCLUSIÓN

Esta versión básica resuelve el problema principal: **eliminar el formato rígido de correo** y dar **transparencia al proceso** mediante una plataforma web simple donde:

- ✅ Proveedores presentan planes directamente
- ✅ Técnicos revisan en un solo lugar
- ✅ Estados visibles para todos
- ✅ Sin dependencias externas complejas
- ✅ Implementable en 4 semanas
- ✅ Costo mínimo de desarrollo

**Siguiente paso:** Una vez validada esta versión básica con usuarios reales, se pueden agregar gradualmente las características avanzadas (notificaciones, IA, integraciones, etc.).