"""
Vistas para estadísticas y dashboards del sistema
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import date, timedelta, datetime
from .models import (
    PerfilUsuario, Proveedor, Evaluacion, 
    PlanMejoramiento, HistorialEstado
)
import json


@login_required
def dashboard_estadisticas(request):
    """Dashboard principal con estadísticas globales del sistema"""
    
    # Verificar que sea gestor o técnico
    if hasattr(request.user, 'perfil'):
        if request.user.perfil.tipo_perfil not in ['GESTOR', 'TECNICO']:
            return redirect('dashboard_proveedor')
    
    # Estadísticas generales
    total_proveedores = Proveedor.objects.filter(activo=True).count()
    total_evaluaciones = Evaluacion.objects.count()
    total_planes = PlanMejoramiento.objects.count()
    
    # Evaluaciones por rango de puntaje (Solo las que requieren plan de mejoramiento)
    evaluaciones_aceptable = Evaluacion.objects.filter(puntaje__gte=60, puntaje__lt=80).count()
    evaluaciones_critico = Evaluacion.objects.filter(puntaje__lt=60).count()

    # Evaluaciones por Sociedad
    evaluaciones_por_sociedad = Evaluacion.objects.exclude(
        sociedad__isnull=True
    ).exclude(sociedad='').values('sociedad').annotate(
        total=Count('id')
    ).order_by('sociedad')

    # Evaluaciones por Tipo de Contrato
    evaluaciones_por_tipo_contrato = Evaluacion.objects.exclude(
        tipo_contrato__isnull=True
    ).exclude(tipo_contrato='').values('tipo_contrato').annotate(
        total=Count('id')
    ).order_by('tipo_contrato')
    
    # Planes por estado
    planes_por_estado = PlanMejoramiento.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')
    
    # Convertir a diccionario para mejor manejo
    estados_dict = {item['estado']: item['total'] for item in planes_por_estado}
    
    # Promedio de puntajes por mes (últimos 6 meses)
    fecha_inicio = date.today() - timedelta(days=180)
    evaluaciones_por_mes = []
    
    for i in range(6):
        mes_actual = fecha_inicio + timedelta(days=30*i)
        mes_siguiente = mes_actual + timedelta(days=30)
        
        promedio = Evaluacion.objects.filter(
            fecha__gte=mes_actual,
            fecha__lt=mes_siguiente
        ).aggregate(promedio=Avg('puntaje'))['promedio'] or 0
        
        evaluaciones_por_mes.append({
            'mes': mes_actual.strftime('%b %Y'),
            'promedio': round(promedio, 1)
        })
    
    # Top 10 proveedores con mejor desempeño
    mejores_proveedores = Evaluacion.objects.values(
        'proveedor__razon_social'
    ).annotate(
        promedio_puntaje=Avg('puntaje'),
        total_evaluaciones=Count('id')
    ).filter(
        total_evaluaciones__gte=1
    ).order_by('-promedio_puntaje')[:10]
    
    # Proveedores con planes pendientes
    planes_pendientes = PlanMejoramiento.objects.filter(
        estado__in=['ENVIADO', 'EN_REVISION', 'ESPERANDO_APROBACION']
    ).select_related('proveedor', 'evaluacion')[:10]
    
    # Planes vencidos o próximos a vencer (5 días)
    fecha_limite = date.today() + timedelta(days=5)
    planes_por_vencer = PlanMejoramiento.objects.filter(
        fecha_limite__lte=fecha_limite,
        estado__in=['BORRADOR', 'REQUIERE_AJUSTES']
    ).select_related('proveedor')
    
    # Estadísticas de criterios de evaluación (promedios)
    criterios_promedio = Evaluacion.objects.aggregate(
        gestion=Avg('puntaje_gestion'),
        calidad=Avg('puntaje_calidad'),
        oportunidad=Avg('puntaje_oportunidad'),
        ambiental_social=Avg('puntaje_ambiental_social'),
        sst=Avg('puntaje_sst')
    )
    
    # Evaluaciones que requieren aprobación especial
    evaluaciones_aprobacion = Evaluacion.objects.filter(
        Q(requiere_aprobacion_sst=True) | Q(requiere_aprobacion_ambiental=True)
    ).select_related('proveedor')[:5]
    
    # Actividad reciente (últimos 7 días)
    fecha_actividad = timezone.now() - timedelta(days=7)
    actividad_reciente = HistorialEstado.objects.filter(
        fecha_cambio__gte=fecha_actividad
    ).select_related('plan__proveedor', 'usuario').order_by('fecha_cambio')[:20]
    
    # Tasa de cumplimiento (planes aprobados vs rechazados)
    planes_aprobados = PlanMejoramiento.objects.filter(estado='APROBADO').count()
    planes_rechazados = PlanMejoramiento.objects.filter(estado='RECHAZADO').count()
    tasa_cumplimiento = 0
    if (planes_aprobados + planes_rechazados) > 0:
        tasa_cumplimiento = round((planes_aprobados / (planes_aprobados + planes_rechazados)) * 100, 1)
    
    # Preparar datos para gráficos (Solo evaluaciones que requieren plan)
    # Formato correcto para Chart.js
    datos_puntaje = {
        'labels': ['Aceptable (60-79)', 'Crítico (<60)'],
        'datasets': [{
            'data': [evaluaciones_aceptable, evaluaciones_critico],
            'backgroundColor': ['#FFA500', '#dc3545']
        }]
    }

    colores_estados = {
        'BORRADOR': '#6c757d',
        'ENVIADO': '#0066CC',
        'FIRMADO_ENVIADO': '#003366',
        'EN_REVISION': '#17a2b8',
        'ESPERANDO_APROBACION': '#FFA500',
        'SOLICITUD_AJUSTES': '#fd7e14',
        'REQUIERE_AJUSTES': '#fd7e14',
        'DOCUMENTOS_REEVALUADOS': '#6f42c1',
        'APROBADO': '#28a745',
        'RECHAZADO': '#dc3545',
        'REEVALUAR': '#6f42c1'
    }

    labels_estados = []
    data_estados = []
    colors_estados = []

    for estado, total in estados_dict.items():
        try:
            labels_estados.append(dict(PlanMejoramiento.ESTADOS).get(estado, estado))
        except Exception:
            labels_estados.append(estado)
        data_estados.append(total)
        colors_estados.append(colores_estados.get(estado, '#6c757d'))

    datos_estados = {
        'labels': labels_estados,
        'datasets': [{
            'data': data_estados,
            'backgroundColor': colors_estados
        }]
    }

    # Datos para gráfico de Sociedad
    colores_sociedad = {
        'ISA': '#003366',
        'ITCO': '#0066CC',
        'TRANSELCA': '#00A0D2'
    }
    datos_sociedad = {
        'labels': [item['sociedad'] for item in evaluaciones_por_sociedad],
        'datasets': [{
            'data': [item['total'] for item in evaluaciones_por_sociedad],
            'backgroundColor': [colores_sociedad.get(item['sociedad'], '#6c757d') for item in evaluaciones_por_sociedad]
        }]
    }

    # Datos para gráfico de Tipo de Contrato
    nombres_tipo_contrato = {
        # Nuevos tipos (numéricos)
        '1': '1 - BIENES SIN SST Y AMB',
        '2': '2 - SERVICIOS SIN SST Y AMB',
        '3': '3 - BIENES Y SERVICIOS SIN SST Y AMB',
        '6': '6 - SERVICIOS SÓLO CON SST',
        '7': '7 - SERVICIOS SÓLO CON AMB',
        '8': '8 - BIENES Y SERVICIOS SÓLO CON SST',
        '9': '9 - BIENES Y SERVICIOS SÓLO CON AMB',
        '10': '10 - BIENES SÓLO CON SST',
        '11': '11 - BIENES SÓLO CON AMB',
        '12': '12 - BIENES CON SST Y AMB',
        # Tipos antiguos (texto)
        'OBRA': 'Obra',
        'SUMINISTRO': 'Suministro',
        'SERVICIO': 'Prestación de Servicios',
        'CONSULTORIA': 'Consultoría',
        'INTERVENTORIA': 'Interventoría',
        'ORDEN_COMPRA': 'Orden de Compra',
        'OBRAS_CIVILES': 'Obras Civiles',
        'SUMINISTRO_EQUIPOS': 'Suministro de Equipos',
        'MONTAJE_ELECTROMECANICO': 'Montaje Electromecánico',
        'SERVICIOS_TECNICOS': 'Servicios Técnicos',
        'MANTENIMIENTO': 'Mantenimiento',
        'ESTUDIOS_DISENOS': 'Estudios y Diseños',
        'TRANSPORTE': 'Transporte',
        'OTRO': 'Otro'
    }
    datos_tipo_contrato = {
        'labels': [nombres_tipo_contrato.get(str(item['tipo_contrato']), str(item['tipo_contrato'])) for item in evaluaciones_por_tipo_contrato],
        'datasets': [{
            'data': [item['total'] for item in evaluaciones_por_tipo_contrato],
            'backgroundColor': ['#003366', '#0066CC', '#00A0D2', '#28a745', '#FFA500', '#dc3545', '#6f42c1', '#fd7e14', '#17a2b8', '#6c757d', '#20c997', '#e83e8c']
        }]
    }

    context = {
        # Estadísticas generales
        'total_proveedores': total_proveedores,
        'total_evaluaciones': total_evaluaciones,
        'total_planes': total_planes,
        'tasa_cumplimiento': tasa_cumplimiento,
        
        # Evaluaciones por puntaje (solo las que requieren plan)
        'evaluaciones_aceptable': evaluaciones_aceptable,
        'evaluaciones_critico': evaluaciones_critico,
        
        # Planes por estado
        'estados_dict': estados_dict,
        'planes_pendientes': planes_pendientes,
        'planes_por_vencer': planes_por_vencer,
        
        # Promedios
        'evaluaciones_por_mes': evaluaciones_por_mes,
        'criterios_promedio': criterios_promedio,
        
        # Rankings
        'mejores_proveedores': mejores_proveedores,
        
        # Alertas
        'evaluaciones_aprobacion': evaluaciones_aprobacion,
        
        # Actividad
        'actividad_reciente': actividad_reciente,
        
        # Datos para gráficos (JSON)
        'datos_puntaje_json': json.dumps(datos_puntaje),
        'datos_estados_json': json.dumps(datos_estados),
        'evaluaciones_por_mes_json': json.dumps(evaluaciones_por_mes),
        'datos_sociedad_json': json.dumps(datos_sociedad),
        'datos_tipo_contrato_json': json.dumps(datos_tipo_contrato),
    }
    
    return render(request, 'planes/dashboard_estadisticas.html', context)


@login_required
def estadisticas_proveedor(request, proveedor_id):
    """Estadísticas detalladas de un proveedor específico"""
    
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    
    # Historial de evaluaciones
    evaluaciones = Evaluacion.objects.filter(
        proveedor=proveedor
    ).order_by('fecha')
    
    # Estadísticas generales
    total_evaluaciones = evaluaciones.count()
    promedio_puntaje = evaluaciones.aggregate(Avg('puntaje'))['puntaje__avg'] or 0
    
    # Evolución del puntaje
    evolucion_puntaje = list(evaluaciones.values('fecha', 'puntaje', 'periodo').order_by('fecha'))
    
    # Planes de mejoramiento
    planes = PlanMejoramiento.objects.filter(proveedor=proveedor)
    total_planes = planes.count()
    planes_aprobados = planes.filter(estado='APROBADO').count()
    planes_rechazados = planes.filter(estado='RECHAZADO').count()
    planes_pendientes = planes.filter(
        estado__in=['ENVIADO', 'EN_REVISION', 'ESPERANDO_APROBACION']
    ).count()
    
    # Promedio por criterio
    criterios_promedio = evaluaciones.aggregate(
        gestion=Avg('puntaje_gestion'),
        calidad=Avg('puntaje_calidad'),
        oportunidad=Avg('puntaje_oportunidad'),
        ambiental_social=Avg('puntaje_ambiental_social'),
        sst=Avg('puntaje_sst')
    )
    
    # Tiempo promedio de respuesta (desde envío hasta aprobación)
    planes_aprobados_obj = planes.filter(
        estado='APROBADO',
        fecha_envio__isnull=False,
        fecha_aprobacion__isnull=False
    )
    
    tiempo_respuesta_promedio = 0
    if planes_aprobados_obj.exists():
        tiempos = [(p.fecha_aprobacion - p.fecha_envio).days for p in planes_aprobados_obj]
        tiempo_respuesta_promedio = sum(tiempos) / len(tiempos)
    
    context = {
        'proveedor': proveedor,
        'evaluaciones': evaluaciones,
        'total_evaluaciones': total_evaluaciones,
        'promedio_puntaje': round(promedio_puntaje, 1),
        'evolucion_puntaje': evolucion_puntaje,
        'total_planes': total_planes,
        'planes_aprobados': planes_aprobados,
        'planes_rechazados': planes_rechazados,
        'planes_pendientes': planes_pendientes,
        'criterios_promedio': criterios_promedio,
        'tiempo_respuesta_promedio': round(tiempo_respuesta_promedio, 1),
        'evolucion_puntaje_json': json.dumps(evolucion_puntaje, default=str),
    }
    
    return render(request, 'planes/estadisticas_proveedor.html', context)