# Instrucciones para Implementar Tipo de Calificación Dinámico

## Resumen de lo Implementado

✅ **Modelo de Datos:**
- `TipoCalificacion`: 12 tipos de calificación cargados desde Excel
- `CriterioEvaluacion`: 416 criterios con puntajes según tipo
- Comando: `python manage.py cargar_criterios_sap --clear`

✅ **API REST:**
- `/api/tipos-calificacion/` - Lista todos los tipos
- `/api/criterios-tipo/<id>/` - Criterios según tipo seleccionado

## Tipos de Calificación Disponibles

1. `BIENES_SIN_SST_Y_AMB` - Bienes sin SST y Ambiental
2. `SERVICIOS_SIN_SST_Y_AMB` - Servicios sin SST y Ambiental
3. `BIENES_Y_SERVICIOS_SIN_SST_Y_AMB` - Bienes y Servicios sin SST y Ambiental
4. `SERVICIOS_CON_SST_Y_AMB` - Servicios con SST y Ambiental
5. `BIENES_Y_SERVICIOS_CON_SST_Y_AMB` - Bienes y Servicios con SST y Ambiental
6. `SERVICIOS_SÓLO_CON_SST` - Servicios solo con SST
7. `SERVICIOS_SÓLO_CON_AMB` - Servicios solo con Ambiental
8. `BIENES_Y_SERVICIOS_SÓLO_CON_SST` - Bienes y Servicios solo con SST
9. `BIENES_Y_SERVICIOS_SÓLO_CON_AMB` - Bienes y Servicios solo con Ambiental
10. `BIENES_SÓLO_CON_SST` - Bienes solo con SST
11. `BIENES_SÓLO_CON_AMB` - Bienes solo con Ambiental
12. `BIENES_CON_SST_Y_AMB` - Bienes con SST y Ambiental

## Estructura de los Criterios

Cada tipo de calificación tiene múltiples criterios, y cada criterio tiene múltiples opciones de respuesta con diferentes puntajes.

### Ejemplo de Criterio:

**CALIDAD DE LOS BIENES SUMINISTRADOS** (ID Criterio: 2)

Opciones de respuesta para `BIENES SIN SST Y AMB`:
1. "Todos los bienes se recibieron a satisfacción..." - **35 puntos**
2. "Algunos bienes presentaron problemas, intervenidos..." - **25 puntos**
3. "Algunos bienes presentaron problemas, NO intervenidos..." - **18 puntos**
4. "Todos los bienes presentaron problemas..." - **0 puntos**

## Cómo Modificar el Template `cargar_evaluacion.html`

### Paso 1: Agregar Selector de Tipo de Calificación

Después de la línea de `Información del Proveedor`, agregar:

```html
<div class="row">
    <div class="col-md-12 mb-3">
        <label for="tipo_calificacion" class="form-label">Tipo de Calificación *</label>
        <select class="form-control" id="tipo_calificacion" name="tipo_calificacion" required>
            <option value="">-- Seleccione el tipo de calificación --</option>
        </select>
        <div class="form-text">
            Seleccione el tipo según si evalúa bienes, servicios, y si incluye SST y/o Ambiental
        </div>
    </div>
</div>
```

### Paso 2: Agregar Contenedor para Criterios Dinámicos

Reemplazar las secciones estáticas de puntajes por:

```html
<div id="criterios-container" class="mt-4">
    <div class="alert alert-warning">
        <i class="bi bi-info-circle"></i>
        Primero seleccione el <strong>Tipo de Calificación</strong> para cargar los criterios correspondientes.
    </div>
</div>

<input type="hidden" id="puntaje_total" name="puntaje" value="0">
```

### Paso 3: Agregar JavaScript para Cargar Criterios Dinámicamente

En la sección `{% block extra_js %}`, agregar:

```javascript
// Cargar tipos de calificación al iniciar
fetch('{% url "api_tipos_calificacion" %}')
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('tipo_calificacion');
        data.tipos.forEach(tipo => {
            const option = document.createElement('option');
            option.value = tipo.id;
            option.textContent = tipo.nombre;
            option.dataset.codigo = tipo.codigo;
            select.appendChild(option);
        });
    });

// Cuando se selecciona un tipo de calificación
document.getElementById('tipo_calificacion').addEventListener('change', function() {
    const tipoId = this.value;

    if (!tipoId) {
        document.getElementById('criterios-container').innerHTML = `
            <div class="alert alert-warning">
                <i class="bi bi-info-circle"></i>
                Primero seleccione el <strong>Tipo de Calificación</strong>.
            </div>
        `;
        return;
    }

    // Mostrar loading
    document.getElementById('criterios-container').innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p>Cargando criterios...</p>
        </div>
    `;

    // Cargar criterios para el tipo seleccionado
    fetch(`/api/criterios-tipo/${tipoId}/`)
        .then(response => response.json())
        .then(data => {
            renderizarCriterios(data.criterios);
            calcularPuntajeTotal();
        });
});

function renderizarCriterios(criterios) {
    const container = document.getElementById('criterios-container');
    let html = '<h5 class="mb-3 p-2 bg-primary text-white rounded">Criterios de Evaluación</h5>';

    criterios.forEach((criterio, index) => {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0">${criterio.descripcion}</h6>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Seleccione la opción que mejor describe la situación *</label>
        `;

        criterio.opciones.forEach(opcion => {
            html += `
                <div class="form-check mb-2">
                    <input class="form-check-input criterio-radio"
                           type="radio"
                           name="criterio_${criterio.id_criterio}"
                           id="criterio_${criterio.id_criterio}_${opcion.id}"
                           value="${opcion.puntuacion}"
                           data-criterio="${criterio.id_criterio}"
                           required
                           onchange="calcularPuntajeTotal()">
                    <label class="form-check-label" for="criterio_${criterio.id_criterio}_${opcion.id}">
                        <span class="badge bg-primary me-2">${opcion.puntuacion} pts</span>
                        ${opcion.respuesta_corta || opcion.respuesta_normal}
                    </label>
                </div>
            `;
        });

        html += `
                    </div>
                </div>
            </div>
        `;
    });

    // Agregar resumen de puntaje
    html += `
        <div class="card bg-light">
            <div class="card-body">
                <h5 class="mb-0">
                    Puntaje Total: <span id="puntaje-display" class="badge bg-success fs-4">0</span> / 100
                </h5>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

function calcularPuntajeTotal() {
    let total = 0;
    const radios = document.querySelectorAll('.criterio-radio:checked');

    radios.forEach(radio => {
        total += parseInt(radio.value);
    });

    document.getElementById('puntaje-display').textContent = total;
    document.getElementById('puntaje_total').value = total;

    // Actualizar color del badge según puntaje
    const badge = document.getElementById('puntaje-display');
    badge.className = 'badge fs-4';
    if (total >= 80) {
        badge.classList.add('bg-success');
    } else if (total >= 60) {
        badge.classList.add('bg-warning');
    } else {
        badge.classList.add('bg-danger');
    }
}
```

## Ventajas de Esta Implementación

1. **Dinámico**: Los criterios cambian según el tipo de evaluación
2. **Correcto**: Usa los puntajes exactos del Excel de SAP
3. **Mantenible**: Los criterios se actualizan desde la BD, no hay que tocar código
4. **Escalable**: Fácil agregar nuevos tipos de calificación
5. **Visual**: Muestra claramente las opciones y el puntaje total en tiempo real

## Actualizar Datos del Excel

Si el Excel cambia, simplemente ejecutar:

```bash
python manage.py cargar_criterios_sap --clear
```

Esto recargará todos los tipos y criterios automáticamente.

## Notas Importantes

1. El campo `puntaje` en la evaluación se calcula automáticamente sumando los puntajes seleccionados
2. Cada criterio tiene un `id_criterio` único dentro del tipo de calificación
3. Las respuestas tienen una versión "normal" (detallada) y una "corta" (resumida)
4. Se recomienda usar la respuesta corta en los radio buttons para mejor UX
5. El sistema valida que se haya seleccionado una opción para cada criterio

---

**Fecha:** 20 de Octubre, 2025
**Versión:** Sistema de Evaluación Dinámica v1.0
