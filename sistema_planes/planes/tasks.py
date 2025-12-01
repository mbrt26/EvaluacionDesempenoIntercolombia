"""
Tareas automáticas (Celery) para el sistema de planes de mejoramiento

IMPORTANTE: Para que estas tareas funcionen, se debe:
1. Instalar Celery: pip install celery redis
2. Configurar Celery en settings.py
3. Ejecutar Redis como broker
4. Ejecutar el worker de Celery: celery -A sistema_planes worker -l info
5. Ejecutar Celery Beat para tareas periódicas: celery -A sistema_planes beat -l info

Estas tareas se ejecutarán automáticamente según la configuración.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import PlanMejoramiento, HistorialEstado
from .workflows import PlanWorkflow


@shared_task
def verificar_planes_sin_respuesta():
    """
    Tarea periódica para verificar planes que llevan 30+ días sin respuesta
    Cambia el estado de FIRMADO_ENVIADO a NO_RECIBIDO automáticamente

    Debe ejecutarse diariamente
    """
    # Obtener planes en estado FIRMADO_ENVIADO
    planes = PlanMejoramiento.objects.filter(estado='FIRMADO_ENVIADO')

    planes_actualizados = 0

    for plan in planes:
        # Verificar si requiere acción automática
        accion = PlanWorkflow.requiere_accion_automatica(plan)

        if accion:
            nuevo_estado, razon = accion

            # Actualizar días sin respuesta
            plan.dias_sin_respuesta = PlanWorkflow.calcular_dias_sin_respuesta(plan)

            # Realizar la transición
            exito, mensaje = PlanWorkflow.transicionar(
                plan=plan,
                nuevo_estado=nuevo_estado,
                usuario=None,  # Acción del sistema
                comentario=f'Acción automática: {razon}'
            )

            if exito:
                planes_actualizados += 1

                # TODO: Enviar notificación por email al gestor y al proveedor
                print(f'Plan {plan.id} cambiado a NO_RECIBIDO automáticamente')

    return f'Verificación completada. {planes_actualizados} planes actualizados a NO_RECIBIDO'


@shared_task
def actualizar_dias_sin_respuesta():
    """
    Tarea periódica para actualizar el contador de días sin respuesta
    en todos los planes activos

    Debe ejecutarse diariamente
    """
    planes = PlanMejoramiento.objects.filter(
        estado__in=['FIRMADO_ENVIADO', 'NO_RECIBIDO']
    )

    planes_actualizados = 0

    for plan in planes:
        if plan.fecha_carta:
            dias = PlanWorkflow.calcular_dias_sin_respuesta(plan)
            if plan.dias_sin_respuesta != dias:
                plan.dias_sin_respuesta = dias
                plan.save(update_fields=['dias_sin_respuesta'])
                planes_actualizados += 1

    return f'Actualización completada. {planes_actualizados} planes actualizados'


@shared_task
def alertar_planes_proximos_vencer():
    """
    Tarea periódica para alertar sobre planes próximos a vencer (5 días o menos)

    Debe ejecutarse diariamente
    """
    from datetime import date

    fecha_limite = date.today() + timedelta(days=5)

    # Obtener planes activos próximos a vencer
    planes = PlanMejoramiento.objects.filter(
        estado__in=['ESPERANDO_APROBACION', 'SOLICITUD_AJUSTES', 'EN_RADICACION'],
        fecha_limite__lte=fecha_limite,
        fecha_limite__gte=date.today()
    )

    alertas_enviadas = 0

    for plan in planes:
        dias_restantes = (plan.fecha_limite - date.today()).days

        # TODO: Enviar notificación por email
        print(f'Alerta: Plan {plan.id} vence en {dias_restantes} días')

        # Crear registro en historial
        HistorialEstado.objects.create(
            plan=plan,
            estado_anterior=plan.estado,
            estado_nuevo=plan.estado,
            usuario=None,
            comentario=f'Alerta automática: Plan próximo a vencer en {dias_restantes} días'
        )

        alertas_enviadas += 1

    return f'Alertas enviadas: {alertas_enviadas} planes próximos a vencer'


@shared_task
def limpiar_historial_antiguo():
    """
    Tarea periódica para limpiar registros muy antiguos del historial
    (opcional - solo si el historial crece demasiado)

    Debe ejecutarse mensualmente
    """
    # Mantener solo historial de los últimos 2 años
    fecha_limite = timezone.now() - timedelta(days=730)

    registros_eliminados = HistorialEstado.objects.filter(
        fecha_cambio__lt=fecha_limite
    ).delete()

    return f'Limpieza completada. {registros_eliminados[0]} registros eliminados'


@shared_task
def generar_reporte_mensual():
    """
    Tarea periódica para generar reportes mensuales de gestión

    Debe ejecutarse el primer día de cada mes
    """
    from django.db.models import Count
    from datetime import date

    # Obtener estadísticas del mes anterior
    hoy = date.today()
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)

    # Contar planes por estado durante el mes anterior
    planes_mes_anterior = PlanMejoramiento.objects.filter(
        fecha_creacion__gte=primer_dia_mes_anterior,
        fecha_creacion__lte=ultimo_dia_mes_anterior
    )

    estadisticas = planes_mes_anterior.values('estado').annotate(
        total=Count('id')
    )

    # TODO: Generar PDF o enviar email con el reporte
    print(f'Reporte mensual generado para {primer_dia_mes_anterior.strftime("%B %Y")}')
    print(f'Total de planes: {planes_mes_anterior.count()}')
    print('Estadísticas por estado:')
    for stat in estadisticas:
        print(f"  - {stat['estado']}: {stat['total']}")

    return f'Reporte mensual generado para {primer_dia_mes_anterior.strftime("%B %Y")}'


# ============= CONFIGURACIÓN DE TAREAS PERIÓDICAS =============
"""
Agregar en settings.py:

from celery.schedules import crontab

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Bogota'

CELERY_BEAT_SCHEDULE = {
    'verificar-planes-sin-respuesta': {
        'task': 'planes.tasks.verificar_planes_sin_respuesta',
        'schedule': crontab(hour=9, minute=0),  # Diariamente a las 9 AM
    },
    'actualizar-dias-sin-respuesta': {
        'task': 'planes.tasks.actualizar_dias_sin_respuesta',
        'schedule': crontab(hour=0, minute=0),  # Diariamente a medianoche
    },
    'alertar-planes-proximos-vencer': {
        'task': 'planes.tasks.alertar_planes_proximos_vencer',
        'schedule': crontab(hour=8, minute=0),  # Diariamente a las 8 AM
    },
    'generar-reporte-mensual': {
        'task': 'planes.tasks.generar_reporte_mensual',
        'schedule': crontab(day_of_month=1, hour=6, minute=0),  # Primer día del mes a las 6 AM
    },
    'limpiar-historial-antiguo': {
        'task': 'planes.tasks.limpiar_historial_antiguo',
        'schedule': crontab(day_of_month=1, hour=2, minute=0),  # Primer día del mes a las 2 AM
    },
}


Y crear el archivo celery.py en el directorio principal del proyecto:

# sistema_planes/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_planes.settings')

app = Celery('sistema_planes')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


Modificar sistema_planes/__init__.py:

from .celery import app as celery_app

__all__ = ('celery_app',)
"""
