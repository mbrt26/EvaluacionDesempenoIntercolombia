"""
Vistas API para obtener criterios de evaluación dinámicos
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import TipoCalificacion, CriterioEvaluacion


@login_required
def obtener_tipos_calificacion(request):
    """
    API para obtener todos los tipos de calificación disponibles
    """
    tipos = TipoCalificacion.objects.filter(activo=True).order_by('nombre')

    data = {
        'tipos': [
            {
                'id': tipo.id,
                'codigo': tipo.codigo,
                'nombre': tipo.nombre,
                'descripcion': tipo.descripcion
            }
            for tipo in tipos
        ]
    }

    return JsonResponse(data)


@login_required
def obtener_criterios_por_tipo(request, tipo_id):
    """
    API para obtener criterios de evaluación según el tipo de calificación
    Agrupa por criterio y devuelve las opciones de respuesta
    """
    tipo = TipoCalificacion.objects.filter(id=tipo_id, activo=True).first()

    if not tipo:
        return JsonResponse({'error': 'Tipo de calificación no encontrado'}, status=404)

    # Obtener todos los criterios para este tipo
    criterios = CriterioEvaluacion.objects.filter(
        tipo_calificacion=tipo,
        activo=True
    ).order_by('id_criterio', '-puntuacion_maxima')

    # Agrupar por id_criterio
    criterios_agrupados = {}

    for criterio in criterios:
        if criterio.id_criterio not in criterios_agrupados:
            criterios_agrupados[criterio.id_criterio] = {
                'id_criterio': criterio.id_criterio,
                'descripcion': criterio.descripcion_criterio,
                'opciones': []
            }

        criterios_agrupados[criterio.id_criterio]['opciones'].append({
            'id': criterio.id,
            'puntuacion': criterio.puntuacion_maxima,
            'respuesta_normal': criterio.respuesta_normal,
            'respuesta_corta': criterio.respuesta_corta
        })

    # Convertir a lista ordenada
    criterios_lista = list(criterios_agrupados.values())

    data = {
        'tipo': {
            'id': tipo.id,
            'codigo': tipo.codigo,
            'nombre': tipo.nombre
        },
        'criterios': criterios_lista
    }

    return JsonResponse(data)
