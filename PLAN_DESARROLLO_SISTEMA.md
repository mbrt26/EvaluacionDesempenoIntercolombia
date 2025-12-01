# Plan de Desarrollo - Sistema de Gestión de Planes de Mejoramiento para Proveedores
## Intercolombia S.A. E.S.P.

---

## 1. RESUMEN EJECUTIVO

### Problema Identificado
Actualmente Intercolombia maneja los planes de mejoramiento de proveedores a través de Power Automate y SharePoint, con las siguientes limitaciones:
- Los proveedores solo pueden interactuar por correo electrónico con estructura muy específica
- Si el proveedor no sigue exactamente el formato del correo, el sistema no lo procesa
- No hay transparencia para el proveedor sobre el estado de su plan
- Los tiempos de respuesta y reevaluación son muy largos (hasta más de 1 año)
- No existe un portal donde los proveedores puedan gestionar directamente sus planes

### Solución Propuesta
Desarrollar un **Sistema Web de Gestión de Planes de Mejoramiento** que permita:
- Portal web para que proveedores accedan con credenciales propias
- Gestión directa de planes de mejoramiento sin depender de correos
- Transparencia total del proceso y estados
- Notificaciones automáticas y recordatorios
- Dashboard para administradores y técnicos
- Integración con sistemas existentes de Intercolombia

---

## 2. ANÁLISIS DE REQUERIMIENTOS

### 2.1 Flujo de Trabajo Actual
1. **Evaluación inicial**: Proveedor obtiene calificación < 80 puntos
2. **Notificación**: Se envía carta al proveedor con la evaluación
3. **Respuesta del proveedor** (5 días hábiles):
   - Puede solicitar aclaración
   - Puede aceptar y presentar plan (20 días hábiles)
   - Puede rechazar plan
4. **Revisión técnica**: El técnico evalúa el plan presentado
5. **Ciclo de ajustes**: Si requiere ajustes, se devuelve al proveedor
6. **Aprobación y radicación**: Plan aprobado y radicado
7. **Reevaluación**: Después de implementar las mejoras

### 2.2 Estados del Sistema
- **En proceso**: Evaluación inicial recibida
- **Firmado y enviado**: Carta enviada al proveedor
- **Esperando aprobación**: Plan recibido, pendiente revisión técnica
- **No recibido**: Proveedor no presentó plan en tiempo
- **Radicado**: Plan aprobado
- **Cancelado**: Proveedor rechazó presentar plan
- **Suspendido**: Por falta de ética (0 puntos)

### 2.3 Actores del Sistema
1. **Proveedores**: Empresas evaluadas que deben presentar planes
2. **Técnicos/Administradores de contrato**: Evalúan y aprueban planes
3. **Administradores del sistema**: Gestión general y configuración
4. **Sistema**: Automatizaciones y notificaciones

---

## 3. ARQUITECTURA TÉCNICA

### 3.1 Stack Tecnológico Recomendado

#### Backend
- **Framework**: Django 5.0 (Python 3.11+)
- **API**: Django REST Framework
- **Base de datos**: PostgreSQL 15
- **Cache**: Redis
- **Tareas asíncronas**: Celery + Redis
- **Autenticación**: Django Auth + JWT para API

#### Frontend
- **Framework**: React 18 o Vue 3
- **UI Components**: Material-UI o Ant Design
- **Estado**: Redux/Zustand o Pinia
- **Gráficos**: Chart.js o Recharts

#### Infraestructura
- **Hosting**: Azure App Service (compatible con ambiente ISA)
- **Storage**: Azure Blob Storage para documentos
- **Email**: SendGrid o Azure Communication Services
- **Monitoreo**: Application Insights

### 3.2 Integraciones
- **SharePoint**: API REST para sincronización de datos
- **Office 365**: Microsoft Graph API para usuarios y correos
- **Power Automate**: Webhooks para eventos críticos
- **Azure AD**: Single Sign-On (SSO) para empleados ISA

---

## 4. MÓDULOS DEL SISTEMA

### 4.1 Módulo de Autenticación y Usuarios
**Funcionalidades:**
- Login para proveedores con credenciales propias
- SSO con Azure AD para empleados ISA
- Gestión de perfiles y permisos
- Recuperación de contraseñas
- Auditoría de accesos

**Modelos de datos:**
```python
- Usuario (extendido de Django User)
- Proveedor (NIT, razón social, contactos)
- TecnicoISA (empleado, área, contratos asignados)
- Rol (permisos y accesos)
- SesionAuditoria (logs de acceso)
```

### 4.2 Módulo de Evaluaciones
**Funcionalidades:**
- Registro de evaluaciones de desempeño
- Cálculo automático de puntajes
- Generación de informes de evaluación
- Histórico de evaluaciones por proveedor

**Modelos de datos:**
```python
- EvaluacionDesempeno (fecha, puntaje, estado)
- CriterioEvaluacion (nombre, peso, descripción)
- DetalleEvaluacion (criterio, puntaje, observaciones)
- DocumentoEvaluacion (tipo, archivo, fecha)
```

### 4.3 Módulo de Planes de Mejoramiento
**Funcionalidades:**
- Creación y edición de planes por parte del proveedor
- Definición de acciones, metas y plazos
- Adjuntar documentos de soporte
- Versionado de planes
- Comentarios y observaciones

**Modelos de datos:**
```python
- PlanMejoramiento (proveedor, evaluacion, estado, version)
- AccionMejora (descripción, meta, indicador, plazo)
- DocumentoPlan (archivo, tipo, fecha_carga)
- ComentarioPlan (usuario, texto, fecha)
- HistorialEstados (estado_anterior, estado_nuevo, fecha)
```

### 4.4 Módulo de Flujo de Trabajo
**Funcionalidades:**
- Motor de estados y transiciones
- Validaciones por estado
- Escalamiento automático
- Gestión de plazos y vencimientos

**Implementación:**
```python
class EstadoPlan:
    EN_PROCESO = 'en_proceso'
    FIRMADO_ENVIADO = 'firmado_enviado'
    ESPERANDO_APROBACION = 'esperando_aprobacion'
    REQUIERE_AJUSTES = 'requiere_ajustes'
    APROBADO = 'aprobado'
    RADICADO = 'radicado'
    NO_RECIBIDO = 'no_recibido'
    CANCELADO = 'cancelado'
    SUSPENDIDO = 'suspendido'
```

### 4.5 Módulo de Notificaciones
**Funcionalidades:**
- Notificaciones por email automáticas
- Recordatorios de vencimientos
- Alertas en el portal web
- Configuración de preferencias por usuario
- Plantillas de correo personalizables

**Tipos de notificaciones:**
- Nueva evaluación recibida
- Plazo próximo a vencer (5, 3, 1 día antes)
- Plan aprobado/rechazado
- Solicitud de ajustes
- Cambios de estado

### 4.6 Portal Web para Proveedores
**Funcionalidades:**
- Dashboard con estado actual de planes
- Formularios intuitivos para crear/editar planes
- Carga de documentos drag & drop
- Historial de comunicaciones
- Descarga de formatos e instructivos
- Chat o mensajería interna con técnicos

**Vistas principales:**
```
/portal/
├── dashboard/
├── evaluaciones/
├── planes/
│   ├── nuevo/
│   ├── editar/{id}/
│   └── historial/
├── documentos/
├── mensajes/
└── perfil/
```

### 4.7 Panel de Administración
**Funcionalidades:**
- Vista consolidada de todos los planes
- Filtros y búsqueda avanzada
- Aprobación/rechazo de planes
- Generación de reportes
- Configuración del sistema
- Gestión de usuarios y permisos

**Dashboards:**
- KPIs principales (planes pendientes, aprobados, vencidos)
- Gráficos de tendencias
- Ranking de proveedores
- Alertas y excepciones

### 4.8 Módulo de Reportes
**Reportes disponibles:**
- Estado general de planes de mejoramiento
- Proveedores con calificación < 60 (requieren aval de tercero)
- Tiempos de respuesta por etapa
- Efectividad de planes implementados
- Historial de reevaluaciones
- Exportación a Excel/PDF

---

## 5. CARACTERÍSTICAS ESPECIALES

### 5.1 Gestión de Casos Especiales
- **Calificación < 60**: Requiere aval de tercero
- **Calificación = 0**: Por falta de ética, suspensión 5 años
- **Solicitudes de aclaración**: Proceso específico de 5 días

### 5.2 Trazabilidad Completa
- Registro de todas las acciones
- Historial de cambios en planes
- Versionado de documentos
- Logs de auditoría

### 5.3 Mejoras sobre Sistema Actual
1. **Eliminación de dependencia del correo**: Portal web directo
2. **Transparencia total**: Proveedor ve estado en tiempo real
3. **Reducción de tiempos**: Notificaciones automáticas y seguimiento
4. **Mejor comunicación**: Chat/mensajería integrada
5. **Datos centralizados**: Un solo lugar para toda la información

---

## 6. PLAN DE IMPLEMENTACIÓN

### Fase 1: Configuración Inicial (2 semanas)
- Configurar ambiente de desarrollo
- Crear estructura del proyecto Django
- Configurar base de datos y modelos iniciales
- Implementar autenticación básica

### Fase 2: Desarrollo Core (4 semanas)
- Módulo de evaluaciones
- Módulo de planes de mejoramiento
- Motor de flujo de trabajo
- Sistema de notificaciones básico

### Fase 3: Portal Proveedores (3 semanas)
- Interfaz de usuario React/Vue
- Formularios de gestión de planes
- Carga de documentos
- Dashboard del proveedor

### Fase 4: Panel Administración (2 semanas)
- Vistas de administración
- Aprobación/rechazo de planes
- Reportes básicos
- Configuración del sistema

### Fase 5: Integraciones (2 semanas)
- Integración con SharePoint
- Conexión con Office 365
- Webhooks con Power Automate
- SSO con Azure AD

### Fase 6: Pruebas y Ajustes (2 semanas)
- Pruebas unitarias y de integración
- Pruebas de usuario (UAT)
- Corrección de errores
- Optimización de rendimiento

### Fase 7: Despliegue (1 semana)
- Configuración en Azure
- Migración de datos existentes
- Capacitación de usuarios
- Go-live y soporte inicial

**Tiempo total estimado: 16 semanas**

---

## 7. ESTRUCTURA DEL PROYECTO

```
gestion-planes-mejoramiento/
├── backend/
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── autenticacion/
│   │   ├── evaluaciones/
│   │   ├── planes/
│   │   ├── flujos/
│   │   ├── notificaciones/
│   │   ├── reportes/
│   │   └── common/
│   ├── static/
│   ├── media/
│   ├── templates/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── utils/
│   ├── public/
│   └── package.json
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── docs/
│   ├── api/
│   ├── user-manual/
│   └── technical/
└── README.md
```

---

## 8. CONSIDERACIONES DE SEGURIDAD

1. **Autenticación robusta**: 2FA opcional para usuarios críticos
2. **Encriptación**: HTTPS obligatorio, encriptación de documentos sensibles
3. **Auditoría**: Log de todas las acciones críticas
4. **Respaldos**: Backup automático diario
5. **Cumplimiento**: GDPR y regulaciones colombianas de protección de datos
6. **Validación**: Sanitización de inputs, prevención de XSS y CSRF
7. **Control de acceso**: Basado en roles y permisos granulares

---

## 9. MÉTRICAS DE ÉXITO

### KPIs del Sistema
- Reducción del 80% en tiempo de gestión de planes
- Eliminación de errores por formato de correo
- Reducción del 60% en tiempo de reevaluación
- 100% de trazabilidad de acciones
- Satisfacción del usuario > 85%

### Métricas Técnicas
- Disponibilidad del sistema > 99.5%
- Tiempo de respuesta < 2 segundos
- Capacidad: 500 usuarios concurrentes
- Backup Recovery Time < 4 horas

---

## 10. PRESUPUESTO ESTIMADO

### Desarrollo (16 semanas)
- 1 Líder Técnico/Arquitecto: $40,000,000 COP
- 2 Desarrolladores Full Stack: $64,000,000 COP
- 1 Diseñador UX/UI (8 semanas): $16,000,000 COP
- **Subtotal desarrollo**: $120,000,000 COP

### Infraestructura (Anual)
- Azure App Service + DB: $2,000,000 COP/mes
- Storage y backups: $500,000 COP/mes
- Servicios adicionales: $500,000 COP/mes
- **Subtotal anual**: $36,000,000 COP

### Otros
- Licencias y herramientas: $5,000,000 COP
- Capacitación: $3,000,000 COP
- Contingencia (10%): $12,800,000 COP

**TOTAL PROYECTO PRIMER AÑO: $176,800,000 COP**

---

## 11. RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Resistencia al cambio por usuarios | Alta | Medio | Capacitación exhaustiva, interfaz intuitiva |
| Integración con sistemas legacy | Media | Alto | Análisis detallado previo, APIs bien documentadas |
| Requerimientos cambiantes | Media | Medio | Metodología ágil, sprints cortos |
| Problemas de rendimiento | Baja | Alto | Pruebas de carga, arquitectura escalable |
| Seguridad de datos | Baja | Muy Alto | Auditorías de seguridad, cumplimiento normativo |

---

## 12. PRÓXIMOS PASOS

1. **Validación con stakeholders** (1 semana)
   - Presentar propuesta a Intercolombia
   - Ajustar según feedback
   - Aprobación final

2. **Formación del equipo** (1 semana)
   - Selección de desarrolladores
   - Definición de roles
   - Kick-off del proyecto

3. **Sprint 0 - Preparación** (1 semana)
   - Configurar ambientes
   - Definir estándares de código
   - Crear backlog detallado

4. **Inicio del desarrollo** 
   - Comenzar con Fase 1 según plan

---

## ANEXOS

### A. Diagrama de Flujo del Proceso
[Se incluiría diagrama visual del flujo de trabajo]

### B. Mockups de Interfaces
[Se incluirían diseños preliminares de las pantallas principales]

### C. Modelo de Datos Detallado
[Se incluiría diagrama ER completo]

### D. Matriz de Permisos por Rol
[Se incluiría tabla detallada de permisos]

---

**Documento elaborado por:** Equipo Técnico Indunnova  
**Fecha:** Agosto 2025  
**Versión:** 1.0