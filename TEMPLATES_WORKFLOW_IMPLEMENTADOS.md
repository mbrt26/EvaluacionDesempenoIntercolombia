# Templates del Workflow de Planes de Mejoramiento

## Resumen de Templates Creados

Se han creado **10 templates HTML** para el flujo completo de gestión de planes de mejoramiento.

---

## 1. Templates Principales

### 1.1 `cambiar_estado.html` ✅
**Ruta:** `/plan/<id>/cambiar-estado/`
**Descripción:** Vista genérica para cambiar el estado de un plan
**Usuarios:** Todos (con permisos)

**Características:**
- Selección dinámica de estados disponibles según permisos
- Campos adicionales que aparecen según el estado seleccionado:
  - **PM_RADICADO**: Campo para número de radicado
  - **RECHAZADO**: Campo para motivo de rechazo
  - **ACLARACION**: Campo para observaciones de aclaración
  - **PROCESO_FIRMAS**: Campo para cargar carta de evaluación
- JavaScript para mostrar/ocultar campos dinámicamente
- Validaciones en frontend y backend
- Panel de ayuda con estados disponibles

---

### 1.2 `radicar_plan.html` ✅
**Ruta:** `/plan/<id>/radicar/`
**Descripción:** Vista específica para radicar un plan (asignar número oficial)
**Usuarios:** Solo Gestor de Compras

**Características:**
- Formulario para asignar número de radicado
- Información completa del plan
- Confirmación mediante JavaScript antes de enviar
- Advertencias sobre irreversibilidad de la acción
- Panel de ayuda explicando qué es radicar
- Validación de formato de número de radicado

---

### 1.3 `rechazar_plan.html` ✅
**Ruta:** `/plan/<id>/rechazar/`
**Descripción:** Vista para rechazar un plan durante radicación
**Usuarios:** Gestor de Compras, Gestor

**Características:**
- Campo obligatorio para motivo de rechazo
- Advertencia destacada sobre las consecuencias
- Diseño con colores de alerta (rojo)
- Información del plan en panel lateral
- Validación de motivo obligatorio

---

### 1.4 `solicitar_aclaracion.html` ✅
**Ruta:** `/plan/<id>/solicitar-aclaracion/`
**Descripción:** Solicitar aclaración cuando un plan no ha sido recibido
**Usuarios:** Técnico, Gestor

**Características:**
- Campo para observaciones de aclaración
- Muestra días sin respuesta
- Información de contacto del proveedor
- Diseño con colores de advertencia (amarillo)
- Historial de comunicaciones previas

---

### 1.5 `enviar_carta.html` ✅
**Ruta:** `/plan/<id>/enviar-carta/`
**Descripción:** Enviar carta de evaluación CS para iniciar proceso de firmas
**Usuarios:** Técnico, Gestor

**Características:**
- Upload de archivo de carta (PDF/Word)
- Campo para comentario adicional
- Información del proveedor (emails)
- Proceso visual de los pasos siguientes
- Validación de archivo obligatorio

---

### 1.6 `marcar_falta_etica.html` ✅
**Ruta:** `/plan/<id>/marcar-falta-etica/`
**Descripción:** Marcar proveedor con falta de ética (suspensión 5 años)
**Usuarios:** Solo Gestor

**Características:**
- **Advertencias críticas** muy destacadas
- Campo obligatorio para motivo de sanción
- **Confirmación doble**:
  1. Escribir la palabra "SUSPENDER"
  2. Checkbox de aceptación
  3. Alert de JavaScript
- Lista de consecuencias de la acción
- Diseño con colores de peligro (rojo)
- Botones grandes para evitar clicks accidentales

---

### 1.7 `historial_plan.html` ✅
**Ruta:** `/plan/<id>/historial/`
**Descripción:** Historial completo de cambios de estado del plan
**Usuarios:** Todos

**Características:**
- Timeline visual de cambios de estado
- Indicador de tipo de flujo (principal/excepción/final)
- Badge de estado activo/finalizado
- Información de usuario que realizó cada cambio
- Comentarios de cada transición
- CSS personalizado para timeline
- Colores según tipo de flujo
- Información de radicación si existe

---

## 2. Templates de Listados

### 2.1 `planes_pendientes_radicacion.html` ✅
**Ruta:** `/planes/pendientes-radicacion/`
**Descripción:** Lista de planes en estado EN_RADICACION
**Usuarios:** Gestor de Compras

**Características:**
- Tabla con todos los planes pendientes
- Información de proveedor, evaluación, puntaje
- Fecha de revisión y revisor
- Botones de acción rápida:
  - Ver detalles
  - Radicar
  - Rechazar
- Contador de planes pendientes
- Badges de color según puntaje
- Responsive con Bootstrap

---

### 2.2 `planes_no_recibidos.html` ✅
**Ruta:** `/planes/no-recibidos/`
**Descripción:** Lista de planes no recibidos después de 30 días
**Usuarios:** Técnico, Gestor

**Características:**
- Tabla con planes en estado NO_RECIBIDO
- **Sistema de colores por urgencia:**
  - Normal (30-45 días): Sin color
  - Amarillo (45-60 días): Requiere atención
  - Rojo (+60 días): Acción urgente
- Badge de días sin respuesta
- Fecha de envío de carta
- Botones de acción:
  - Ver detalles
  - Solicitar aclaración
  - Ver historial
- Leyenda de colores
- Contador total de planes no recibidos

---

## 3. Snippet para Integración

### 3.1 `workflow_buttons_snippet.html` ✅
**Descripción:** Componente para agregar a `ver_plan.html`
**Ubicación:** Insertar después de las tarjetas de información del plan

**Características:**
- Botones contextuales según tipo de usuario:
  - **Proveedor:** Editar, confirmar envío, responder aclaración
  - **Técnico/Gestor:** Enviar carta, aprobar, solicitar ajustes
  - **Gestor de Compras:** Radicar, rechazar, cancelar radicación
- Botón "Ver Historial" para todos
- Alertas informativas según estado
- Botón genérico "Cambiar Estado"
- Información adicional del workflow:
  - Número de radicado (si existe)
  - Días sin respuesta
  - Estado de suspensión
- Responsive y con iconos Bootstrap Icons

---

## 4. Integración con `ver_plan.html`

Para integrar los botones de workflow en el template existente:

1. Abrir `/templates/planes/ver_plan.html`
2. Buscar la sección donde terminan las tarjetas de información
3. Agregar el contenido de `workflow_buttons_snippet.html`
4. Asegurarse de que las variables de contexto estén disponibles:
   - `es_proveedor`
   - `es_tecnico`
   - `es_gestor`
   - `es_gestor_compras`

---

## 5. Estilos y Dependencias

### Framework CSS:
- **Bootstrap 5.x** (requerido)
- **Bootstrap Icons** (requerido)

### JavaScript:
Varios templates incluyen JavaScript inline para:
- Validaciones de formulario
- Confirmaciones antes de acciones críticas
- Mostrar/ocultar campos dinámicamente
- Prevenir doble envío de formularios

### Colores y Badges:

| Estado | Color | Clase Bootstrap |
|--------|-------|----------------|
| PROCESO_FIRMAS | Azul | bg-primary |
| FIRMADO_ENVIADO | Info | bg-info |
| ESPERANDO_APROBACION | Advertencia | bg-warning |
| EN_RADICACION | Advertencia | bg-warning |
| PM_RADICADO | Éxito | bg-success |
| NO_RECIBIDO | Secundario | bg-secondary |
| ACLARACION | Advertencia | bg-warning |
| RECHAZADO | Peligro | bg-danger |
| FALTA_ETICA | Peligro | bg-danger |
| PM_REEVALUADO | Éxito | bg-success |
| FIN | Éxito | bg-success |

---

## 6. Flujo de Usuario por Rol

### Proveedor:
1. Ve sus planes en dashboard
2. Clic en plan → Ver detalles
3. Si está en BORRADOR/REQUIERE_AJUSTES → Puede editar
4. Si está en PROCESO_FIRMAS → Confirmar envío firmado
5. Si está en ACLARACION → Responder aclaración
6. Ver historial en cualquier momento

### Técnico/Gestor:
1. Panel técnico → Lista de planes
2. Clic en plan → Ver detalles
3. Botones disponibles según estado:
   - Enviar carta de evaluación
   - Confirmar recepción
   - Solicitar aclaración
   - Aprobar para radicación
   - Solicitar ajustes
   - Marcar falta de ética (solo Gestor)
4. Cambiar estado genérico
5. Ver historial completo

### Gestor de Compras:
1. Dashboard → Planes pendientes de radicación
2. Lista de planes EN_RADICACION
3. Para cada plan:
   - Ver detalles completos
   - Radicar (asignar número)
   - Rechazar (con motivo)
4. Si rechazado → Cancelar radicación
5. Ver historial y seguimiento

---

## 7. Validaciones Implementadas

### Frontend (JavaScript):
- Confirmación antes de acciones irreversibles
- Validación de campos obligatorios
- Validación de palabra clave "SUSPENDER"
- Prevención de doble envío
- Mostrar/ocultar campos dinámicamente

### Backend (Django):
- Validación de permisos por rol
- Validación de transiciones permitidas
- Validación de campos obligatorios
- Validación de estado actual del plan
- Creación de registros en historial

---

## 8. Mensajes y Notificaciones

### Sistema de Mensajes Django:
- `messages.success()` - Acciones exitosas
- `messages.error()` - Errores o falta de permisos
- `messages.warning()` - Advertencias
- `messages.info()` - Información general

### Alertas en Templates:
- `alert-success` - Confirmaciones
- `alert-danger` - Advertencias críticas
- `alert-warning` - Acciones requeridas
- `alert-info` - Información adicional
- `alert-secondary` - Estado neutral

---

## 9. Iconos Utilizados

| Acción | Icono | Clase Bootstrap Icon |
|--------|-------|---------------------|
| Ver | Ojo | bi-eye |
| Editar | Lápiz | bi-pencil |
| Enviar | Sobre | bi-send / bi-envelope |
| Aprobar | Check | bi-check-circle |
| Rechazar | X | bi-x-circle |
| Radicar | Carpeta | bi-folder-check |
| Aclaración | Chat | bi-chat-dots |
| Historial | Reloj | bi-clock-history |
| Cambiar Estado | Flechas | bi-arrow-left-right |
| Peligro | Octágono | bi-exclamation-octagon |
| Advertencia | Triángulo | bi-exclamation-triangle |
| Info | Círculo i | bi-info-circle |
| Configuración | Engranaje | bi-gear |

---

## 10. Responsive Design

Todos los templates están optimizados para:
- **Desktop** (>992px): Layout completo con sidebars
- **Tablet** (768px-991px): Layout ajustado
- **Mobile** (<768px): Stack vertical, botones full-width

Clases responsive de Bootstrap utilizadas:
- `col-md-*` para columnas
- `d-none d-md-block` para ocultar en móvil
- `btn-group` con orientación automática
- `table-responsive` para tablas

---

## 11. Accesibilidad

Implementaciones de accesibilidad:
- Atributo `aria-label` en breadcrumbs
- Etiquetas `<label>` asociadas a inputs
- Estructura semántica HTML5
- Contraste de colores según WCAG 2.1
- Botones con texto descriptivo
- Formularios con `form-text` explicativos

---

## 12. Testing Recomendado

### Tests por Template:

1. **cambiar_estado.html**
   - Verificar campos dinámicos según estado seleccionado
   - Validar JavaScript de confirmación
   - Probar con diferentes roles

2. **radicar_plan.html**
   - Validar formato de número de radicado
   - Confirmar doble confirmación
   - Verificar solo acceso de Gestor Compras

3. **rechazar_plan.html**
   - Validar motivo obligatorio
   - Probar con diferentes longitudes de texto

4. **solicitar_aclaracion.html**
   - Verificar que muestre días sin respuesta
   - Validar observaciones obligatorias

5. **enviar_carta.html**
   - Probar upload de diferentes tipos de archivo
   - Validar archivo obligatorio

6. **marcar_falta_etica.html**
   - Validar palabra "SUSPENDER" exacta
   - Verificar todas las confirmaciones
   - Solo acceso de Gestor

7. **historial_plan.html**
   - Verificar timeline se renderiza correctamente
   - Probar con diferente cantidad de cambios

8. **planes_pendientes_radicacion.html**
   - Verificar tabla con 0 planes
   - Verificar tabla con múltiples planes
   - Probar botones de acción rápida

9. **planes_no_recibidos.html**
   - Verificar colores según días
   - Probar con diferentes rangos de días

10. **workflow_buttons_snippet.html**
    - Probar con cada rol de usuario
    - Verificar con cada estado posible

---

## 13. Próximas Mejoras Sugeridas

### Futuras Implementaciones:
- [ ] Integrar firma digital de documentos
- [ ] Notificaciones en tiempo real (WebSockets)
- [ ] Exportar historial a PDF
- [ ] Gráfico visual del flujo de estados
- [ ] Dashboard de métricas de tiempo por estado
- [ ] Filtros avanzados en listas
- [ ] Búsqueda por número de radicado
- [ ] Integración con app de reevaluación
- [ ] Notificaciones por email automáticas
- [ ] Recordatorios de fechas límite

---

## 14. Archivos Creados

### Lista Completa de Templates:
```
templates/planes/
├── cambiar_estado.html                    ✅
├── radicar_plan.html                      ✅
├── rechazar_plan.html                     ✅
├── solicitar_aclaracion.html              ✅
├── enviar_carta.html                      ✅
├── marcar_falta_etica.html                ✅
├── historial_plan.html                    ✅
├── planes_pendientes_radicacion.html      ✅
├── planes_no_recibidos.html               ✅
└── workflow_buttons_snippet.html          ✅
```

**Total:** 10 archivos HTML creados

---

## 15. Instrucciones de Integración

### Paso 1: Verificar Base Template
Asegurarse de que `base.html` incluye:
- Bootstrap 5.x CSS
- Bootstrap Icons
- jQuery (si es necesario)
- Block `extra_css` para estilos adicionales
- Block `extra_js` para JavaScript adicional

### Paso 2: Actualizar ver_plan.html
1. Abrir `templates/planes/ver_plan.html`
2. Buscar donde terminan las cards de información
3. Copiar contenido de `workflow_buttons_snippet.html`
4. Pegar antes del cierre del content block

### Paso 3: Verificar Context Variables
En las vistas asegurarse de pasar:
```python
context = {
    'plan': plan,
    'es_proveedor': es_proveedor,
    'es_tecnico': es_tecnico,
    'es_gestor': es_gestor,
    'es_gestor_compras': es_gestor_compras,
    # ... otros datos
}
```

### Paso 4: Probar Navegación
Verificar que todas las URLs estén correctamente configuradas en `urls.py`

---

**Fecha de Implementación:** 20 de Octubre, 2025
**Versión:** 2.0 - Templates del Workflow Completo
