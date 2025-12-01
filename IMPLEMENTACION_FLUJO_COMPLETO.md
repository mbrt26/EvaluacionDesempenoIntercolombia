# Implementación del Flujo Completo de Gestión de Planes de Mejoramiento

## Resumen de Cambios Implementados

Se ha implementado el flujo completo de gestión de planes de mejoramiento basado en el diagrama de estados proporcionado.

---

## 1. Modelo de Datos Actualizado

### Nuevos Estados en `PlanMejoramiento`

#### Flujo Principal (Camino Exitoso - Azul):
- `PROCESO_FIRMAS` - Proceso de Firmas
- `FIRMADO_ENVIADO` - Firmado y Enviado
- `ESPERANDO_APROBACION` - Esperando Aprobación
- `EN_RADICACION` - En Radicación
- `PM_RADICADO` - PM Radicado
- `PM_REEVALUADO` - PM Reevaluado

#### Flujo de Excepciones (Alternativas - Gris):
- `NO_RECIBIDO` - No Recibido (después de 30 días)
- `ACLARACION` - Aclaración
- `EP_REEVALUADO` - EP Reevaluado
- `SOLICITUD_AJUSTES` - Solicitud de Ajustes
- `RECHAZADO` - Rechazado
- `CANCELACION_RADICADA` - Cancelación Radicada
- `FALTA_ETICA` - Falta de Ética

#### Estado Final:
- `FIN` - Fin

### Nuevos Campos Agregados:

```python
- numero_radicado: CharField - Número de radicado asignado
- fecha_radicacion: DateTimeField - Fecha de radicación
- carta_evaluacion: FileField - Carta de evaluación CS
- fecha_carta: DateTimeField - Fecha de envío de carta
- dias_sin_respuesta: IntegerField - Contador de días sin respuesta
- proveedor_suspendido: BooleanField - Marca de suspensión por ética
- fecha_suspension: DateField - Fecha de suspensión
- motivo_rechazo: TextField - Motivo de rechazo del plan
- fecha_aclaracion: DateTimeField - Fecha de aclaración
- observaciones_aclaracion: TextField - Observaciones de aclaración
```

---

## 2. Sistema de Workflow (`workflows.py`)

### Clase `PlanWorkflow`

Maneja toda la lógica de transiciones de estados:

#### Características Principales:

1. **Matriz de Transiciones Permitidas**
   - Define qué estados pueden cambiar a qué otros estados
   - Ejemplo: `PROCESO_FIRMAS` → `FIRMADO_ENVIADO` o `FALTA_ETICA`

2. **Control de Permisos por Rol**
   - Define qué usuarios pueden realizar cada transición
   - Roles: `PROVEEDOR`, `TECNICO`, `GESTOR`, `GESTOR_COMPRAS`, `SISTEMA`

3. **Métodos Principales:**
   - `puede_transicionar()` - Valida si una transición es válida
   - `tiene_permiso()` - Verifica permisos del usuario
   - `transicionar()` - Realiza la transición con validaciones
   - `obtener_proximos_estados()` - Obtiene estados disponibles para un usuario
   - `calcular_dias_sin_respuesta()` - Calcula días transcurridos
   - `requiere_accion_automatica()` - Verifica acciones automáticas necesarias

---

## 3. Nuevas Vistas (`views_workflow.py`)

### Vistas de Cambio de Estado:

1. **`cambiar_estado_plan(plan_id)`**
   - Vista genérica para cambiar estado de un plan
   - Valida permisos y transiciones usando PlanWorkflow

2. **`radicar_plan(plan_id)`**
   - Para Gestor de Compras
   - Asigna número de radicado y cambia a `PM_RADICADO`

3. **`rechazar_plan(plan_id)`**
   - Para Gestor/Gestor de Compras
   - Rechaza un plan con motivo

4. **`solicitar_aclaracion(plan_id)`**
   - Para Técnico/Gestor
   - Solicita aclaración cuando plan no es recibido

5. **`enviar_carta_evaluacion(plan_id)`**
   - Para Gestor/Técnico
   - Inicia proceso de firmas enviando carta CS

6. **`marcar_falta_etica(plan_id)`**
   - Solo para Gestores
   - Marca proveedor con falta de ética (suspensión 5 años)

### Vistas de Consulta:

7. **`historial_plan(plan_id)`**
   - Historial completo de cambios de estado

8. **`planes_pendientes_radicacion()`**
   - Lista de planes pendientes de radicar (para Gestor Compras)

9. **`planes_no_recibidos()`**
   - Lista de planes no recibidos después de 30 días

### API AJAX:

10. **`obtener_proximos_estados_ajax(plan_id)`**
    - Retorna JSON con estados disponibles para un plan

---

## 4. URLs Agregadas

```python
# Workflow y transiciones
/plan/<id>/cambiar-estado/
/plan/<id>/radicar/
/plan/<id>/rechazar/
/plan/<id>/solicitar-aclaracion/
/plan/<id>/enviar-carta/
/plan/<id>/marcar-falta-etica/
/plan/<id>/historial/
/planes/pendientes-radicacion/
/planes/no-recibidos/

# API
/api/plan/<id>/proximos-estados/
```

---

## 5. Tareas Automáticas (Celery) - `tasks.py`

### Tareas Periódicas Configuradas:

1. **`verificar_planes_sin_respuesta()`**
   - Frecuencia: Diaria (9 AM)
   - Función: Cambia planes de `FIRMADO_ENVIADO` a `NO_RECIBIDO` después de 30 días

2. **`actualizar_dias_sin_respuesta()`**
   - Frecuencia: Diaria (medianoche)
   - Función: Actualiza contador de días sin respuesta

3. **`alertar_planes_proximos_vencer()`**
   - Frecuencia: Diaria (8 AM)
   - Función: Alerta sobre planes próximos a vencer (≤5 días)

4. **`generar_reporte_mensual()`**
   - Frecuencia: Mensual (día 1, 6 AM)
   - Función: Genera reporte de estadísticas del mes

5. **`limpiar_historial_antiguo()`**
   - Frecuencia: Mensual (día 1, 2 AM)
   - Función: Elimina historial > 2 años

---

## 6. Migraciones Aplicadas

Se creó la migración `0010_planmejoramiento_carta_evaluacion_and_more.py`:
- ✅ Agregados 10 nuevos campos al modelo
- ✅ Actualizado campo `estado` con nuevos valores
- ✅ Migración aplicada exitosamente a la base de datos

---

## 7. Matriz de Permisos por Transición

| Transición | Roles Permitidos |
|-----------|------------------|
| BORRADOR → PROCESO_FIRMAS | PROVEEDOR |
| PROCESO_FIRMAS → FIRMADO_ENVIADO | PROVEEDOR |
| FIRMADO_ENVIADO → ESPERANDO_APROBACION | TECNICO, GESTOR |
| FIRMADO_ENVIADO → NO_RECIBIDO | SISTEMA (automático) |
| NO_RECIBIDO → ACLARACION | TECNICO, GESTOR |
| ACLARACION → ESPERANDO_APROBACION | PROVEEDOR |
| ACLARACION → EP_REEVALUADO | SISTEMA (integración) |
| ESPERANDO_APROBACION → SOLICITUD_AJUSTES | TECNICO, GESTOR |
| ESPERANDO_APROBACION → EN_RADICACION | TECNICO, GESTOR |
| EN_RADICACION → PM_RADICADO | GESTOR_COMPRAS |
| EN_RADICACION → RECHAZADO | GESTOR_COMPRAS |
| RECHAZADO → CANCELACION_RADICADA | GESTOR_COMPRAS |
| PM_RADICADO → PM_REEVALUADO | SISTEMA (integración) |
| PROCESO_FIRMAS → FALTA_ETICA | GESTOR |

---

## 8. Flujo Completo del Proceso

### Camino Principal (Exitoso):

```
INICIO (Evaluación < 80 puntos)
    ↓
PROCESO_FIRMAS (CS envía carta)
    ↓
FIRMADO_ENVIADO (Proveedor firma y envía)
    ↓
ESPERANDO_APROBACION (Se recibe el plan)
    ↓
EN_RADICACION (Se aprueba)
    ↓
PM_RADICADO (Gestor Compras asigna número)
    ↓
PM_REEVALUADO (App externa reevalúa)
    ↓
FIN
```

### Caminos Alternativos:

- **No recibido en 30 días**: `FIRMADO_ENVIADO` → `NO_RECIBIDO` → `ACLARACION`
- **Requiere ajustes**: `ESPERANDO_APROBACION` → `SOLICITUD_AJUSTES` → (vuelta a) `ESPERANDO_APROBACION`
- **Rechazo**: `EN_RADICACION` → `RECHAZADO` → `CANCELACION_RADICADA` → `FIN`
- **Falta de ética**: `PROCESO_FIRMAS` → `FALTA_ETICA` → `FIN` (suspensión 5 años)

---

## 9. Instalación y Configuración

### Para Tareas Automáticas (Opcional):

```bash
# 1. Instalar dependencias
pip install celery redis

# 2. Instalar y ejecutar Redis
# Ubuntu/Debian:
sudo apt-get install redis-server
sudo service redis-server start

# 3. Ejecutar Celery Worker
celery -A sistema_planes worker -l info

# 4. Ejecutar Celery Beat (tareas periódicas)
celery -A sistema_planes beat -l info
```

### Configuración en `settings.py` (ver `tasks.py` para detalles)

---

## 10. Próximos Pasos Recomendados

### Templates (Pendiente):
- [ ] Crear templates HTML para las nuevas vistas
- [ ] Actualizar templates existentes para mostrar nuevos estados
- [ ] Agregar botones de transición según permisos del usuario
- [ ] Dashboard visual del flujo de estados

### Notificaciones (Pendiente):
- [ ] Configurar envío de emails en transiciones importantes
- [ ] Notificaciones en la aplicación (toasts/alerts)
- [ ] SMS para alertas críticas (opcional)

### Integraciones (Pendiente):
- [ ] API para integración con app de reevaluación de proveedores
- [ ] Webhook para recibir actualizaciones de reevaluación
- [ ] Sincronización de datos entre sistemas

### Mejoras:
- [ ] Exportar flujo de estados a PDF/Excel
- [ ] Gráficos de estado del flujo (progress bar)
- [ ] Dashboard de métricas de tiempo por estado
- [ ] Firma digital de documentos

---

## 11. Archivos Creados/Modificados

### Creados:
- ✅ `planes/workflows.py` - Lógica de transiciones
- ✅ `planes/views_workflow.py` - Vistas de workflow
- ✅ `planes/tasks.py` - Tareas automáticas Celery
- ✅ `planes/migrations/0010_planmejoramiento_carta_evaluacion_and_more.py`

### Modificados:
- ✅ `planes/models.py` - Nuevos estados y campos
- ✅ `planes/urls.py` - Nuevas rutas
- ✅ `planes/views.py` - Import de workflows

---

## 12. Testing

### Casos de Prueba Recomendados:

1. **Flujo completo exitoso**
   - Crear evaluación < 80
   - Enviar carta → Firmar → Aprobar → Radicar → Reevaluar

2. **Plan no recibido**
   - Esperar 30 días (o simular)
   - Verificar cambio automático a NO_RECIBIDO

3. **Solicitud de ajustes**
   - Rechazar plan en aprobación
   - Proveedor corrige y reenvía

4. **Rechazo y cancelación**
   - Rechazar plan en radicación
   - Cancelar radicación

5. **Falta de ética**
   - Marcar proveedor suspendido
   - Verificar que no puede crear nuevos planes

6. **Permisos**
   - Verificar que cada rol solo puede realizar sus transiciones
   - Intentar transiciones no permitidas

---

## 13. Notas Importantes

⚠️ **Compatibilidad con Estados Anteriores:**
Los estados legacy (`EN_REVISION`, `REQUIERE_AJUSTES`, `APROBADO`) se mantienen para compatibilidad con planes existentes.

⚠️ **Transiciones del Sistema:**
Algunas transiciones requieren integración con sistemas externos (app de reevaluación). Estas se marcan como `SISTEMA` en permisos.

⚠️ **Celery Opcional:**
Las tareas automáticas son opcionales. El sistema funciona sin Celery, pero requiere gestión manual de:
- Planes no recibidos después de 30 días
- Alertas de vencimiento
- Reportes mensuales

---

## 14. Contacto y Soporte

Para dudas o problemas con la implementación, revisar:
- Código en `planes/workflows.py` - Documentación inline
- Logs de Celery para tareas automáticas
- Historial de cambios en cada plan

---

**Fecha de Implementación:** 20 de Octubre, 2025
**Versión:** 2.0 - Flujo Completo de Gestión
