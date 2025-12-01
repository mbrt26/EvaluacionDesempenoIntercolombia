"""
Vistas para el sistema de planes de mejoramiento
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F, Max, Min
from django.db import transaction
from datetime import date, timedelta, datetime
from collections import defaultdict
import json
from .models import (
    Proveedor, Evaluacion, PlanMejoramiento,
    DocumentoPlan, AccionMejora, HistorialEstado
)
from .forms import (
    PlanMejoramientoForm, AccionMejoraFormSet,
    RevisionPlanForm, LoginForm
)
from .workflows import PlanWorkflow


# ============= VISTAS DE AUTENTICACIÓN =============

def login_view(request):
    """Vista de login para proveedores y técnicos"""
    if request.user.is_authenticated:
        return redirect('redirect_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.get_full_name() or user.username}')
            
            # Redireccionar según el tipo de usuario
            if hasattr(user, 'proveedor'):
                return redirect('proveedor_dashboard')
            else:
                return redirect('tecnico_panel')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'planes/login.html')


def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente')
    return redirect('login')


@login_required
def redirect_dashboard(request):
    """Redirecciona al dashboard apropiado según el tipo de usuario"""
    if hasattr(request.user, 'proveedor'):
        return redirect('proveedor_dashboard')
    else:
        return redirect('tecnico_panel')


# ============= VISTAS DEL PROVEEDOR =============

@login_required
def dashboard_proveedor(request):
    """Dashboard principal del proveedor"""
    try:
        proveedor = request.user.proveedor
    except:
        messages.error(request, 'No tiene permisos de proveedor')
        return redirect('login')

    # Obtener todas las evaluaciones
    evaluaciones = Evaluacion.objects.filter(
        proveedor=proveedor
    ).order_by('fecha')

    # Estadísticas generales
    total_evaluaciones = evaluaciones.count()
    promedio_puntaje = evaluaciones.aggregate(Avg('puntaje'))['puntaje__avg'] or 0

    # Obtener todos los planes
    planes = PlanMejoramiento.objects.filter(proveedor=proveedor).order_by('fecha_creacion')
    total_planes = planes.count()

    # Planes por estado
    planes_borrador = planes.filter(estado='BORRADOR').count()
    planes_enviados = planes.filter(estado='ENVIADO').count()
    planes_revision = planes.filter(estado__in=['EN_REVISION', 'ESPERANDO_APROBACION']).count()
    planes_requiere_ajustes = planes.filter(estado='REQUIERE_AJUSTES').count()
    planes_aprobados = planes.filter(estado='APROBADO').count()
    planes_rechazados = planes.filter(estado='RECHAZADO').count()

    # Evaluaciones por categoría de puntaje
    # Solo evaluaciones que requieren plan de mejoramiento (puntaje < 80)
    evaluaciones_satisfactorias = 0  # No se cargan al sistema
    evaluaciones_aceptables = evaluaciones.filter(puntaje__gte=60, puntaje__lt=80).count()
    evaluaciones_criticas = evaluaciones.filter(puntaje__lt=60).count()

    context = {
        'proveedor': proveedor,
        'evaluaciones': evaluaciones,
        'planes': planes,
        'estadisticas': {
            'total_evaluaciones': total_evaluaciones,
            'promedio_puntaje': round(promedio_puntaje, 1),
            'total_planes': total_planes,
            'planes_borrador': planes_borrador,
            'planes_enviados': planes_enviados,
            'planes_revision': planes_revision,
            'planes_requiere_ajustes': planes_requiere_ajustes,
            'planes_aprobados': planes_aprobados,
            'planes_rechazados': planes_rechazados,
            'evaluaciones_satisfactorias': evaluaciones_satisfactorias,
            'evaluaciones_aceptables': evaluaciones_aceptables,
            'evaluaciones_criticas': evaluaciones_criticas,
        }
    }

    return render(request, 'planes/dashboard_proveedor.html', context)


@login_required
def ver_evaluacion(request, evaluacion_id):
    """Vista para ver el detalle de una evaluación"""
    # Verificar si es proveedor
    es_proveedor = hasattr(request.user, 'proveedor')
    if es_proveedor:
        # Si es proveedor, solo puede ver sus propias evaluaciones
        proveedor = request.user.proveedor
        evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id, proveedor=proveedor)
        es_gestor = False
        es_tecnico = False
    else:
        # Si es técnico o gestor, puede ver cualquier evaluación
        evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id)
        # Verificar si es gestor o técnico
        es_gestor = hasattr(request.user, 'perfil') and request.user.perfil.es_gestor
        es_tecnico = hasattr(request.user, 'perfil') and request.user.perfil.es_tecnico

    # Obtener el plan asociado si existe
    plan = evaluacion.planes.first()

    # Obtener proveedor
    proveedor = evaluacion.proveedor

    # Calcular días sin recibir plan de mejoramiento (necesario para validaciones)
    dias_sin_plan = 0
    if evaluacion.fecha_cambio_estado_flujo:
        dias_sin_plan = (date.today() - evaluacion.fecha_cambio_estado_flujo.date()).days
    elif evaluacion.fecha_envio_notificacion:
        dias_sin_plan = (date.today() - evaluacion.fecha_envio_notificacion.date()).days

    # Procesar cambio de estado de firma (solo técnicos y gestores)
    if request.method == 'POST' and (es_gestor or es_tecnico):
        if 'cambiar_estado_firma' in request.POST:
            nuevo_estado_firma = request.POST.get('estado_firma')
            observaciones_firma = request.POST.get('observaciones_firma', '')

            if nuevo_estado_firma and nuevo_estado_firma in dict(Evaluacion.ESTADOS_FIRMA):
                fecha_actual = timezone.now()

                # Agregar fecha automáticamente a las observaciones
                if observaciones_firma:
                    observaciones_firma = f"[{fecha_actual.strftime('%d/%m/%Y %H:%M')}] {observaciones_firma}"
                else:
                    observaciones_firma = f"[{fecha_actual.strftime('%d/%m/%Y %H:%M')}] Estado actualizado a {dict(Evaluacion.ESTADOS_FIRMA)[nuevo_estado_firma]}"

                evaluacion.estado_firma = nuevo_estado_firma
                evaluacion.fecha_cambio_estado_firma = fecha_actual
                evaluacion.observaciones_firma = observaciones_firma

                # Si el estado es FIRMADO, generar notificación simulada
                if nuevo_estado_firma == 'FIRMADO':
                    evaluacion.fecha_envio_notificacion = fecha_actual

                    # Verificar si el proveedor tiene usuario
                    tiene_usuario = evaluacion.proveedor.user is not None
                    estado_usuario = "Usuario existente" if tiene_usuario else "Usuario por crear"

                    # Verificar si el siguiente paso del proceso es "Falta de Ética"
                    if evaluacion.estado_flujo_evaluacion == 'FALTA_ETICA':
                        # Notificación especial para Falta de Ética
                        resumen = f"""
NOTIFICACIÓN SIMULADA - Suspensión por Falta de Ética
Fecha: {fecha_actual.strftime('%d/%m/%Y %H:%M')}
Proveedor: {evaluacion.proveedor.razon_social}
NIT: {evaluacion.proveedor.nit}
Periodo: {evaluacion.periodo or 'N/A'}
Puntaje: {evaluacion.puntaje}/100

CONDICIÓN: La evaluación indica "Falta de Ética"

ACCIÓN: El proveedor queda suspendido por 5 años para futuras convocatorias o procesos de contratación.

ESTADO GENERADO: Falta de Ética

RESPONSABLE: Automático

FIN DEL FLUJO: El caso se cierra inmediatamente.

Mensaje:
Estimado proveedor,

Se le informa que como resultado de la evaluación de desempeño del periodo {evaluacion.periodo or 'actual'}, se ha identificado una falta de ética grave.

En consecuencia, su empresa queda SUSPENDIDA por un periodo de 5 años para participar en futuras convocatorias o procesos de contratación con Intercolombia S.A. E.S.P.

Este proceso se cierra de manera definitiva.

Saludos,
Intercolombia S.A. E.S.P.
                        """
                    else:
                        # Notificación normal
                        resumen = f"""
NOTIFICACIÓN SIMULADA - Carta de Evaluación de Desempeño
Fecha: {fecha_actual.strftime('%d/%m/%Y %H:%M')}
Proveedor: {evaluacion.proveedor.razon_social}
NIT: {evaluacion.proveedor.nit}
Periodo: {evaluacion.periodo or 'N/A'}
Puntaje: {evaluacion.puntaje}/100
Estado Usuario: {estado_usuario}

Mensaje:
Estimado proveedor,

Se ha completado la evaluación de desempeño correspondiente al periodo {evaluacion.periodo or 'actual'}.
Su puntaje obtenido es de {evaluacion.puntaje}/100 puntos.

{"Dado que el puntaje es inferior a 80 puntos, debe presentar un Plan de Mejoramiento." if evaluacion.puntaje < 80 else "Felicitaciones por su desempeño satisfactorio."}

Puede acceder al sistema con las siguientes credenciales:
Usuario: {evaluacion.proveedor.nit}
{"Contraseña: (enviada por separado)" if not tiene_usuario else "Contraseña: (usar credenciales existentes)"}

Acceso: http://localhost:9005/

Saludos,
Intercolombia S.A. E.S.P.
                        """

                    evaluacion.resumen_notificacion = resumen.strip()

                evaluacion.save()

                messages.success(request, f'Estado de firma actualizado a: {evaluacion.get_estado_firma_display()}')
                if nuevo_estado_firma == 'FIRMADO':
                    messages.info(request, 'Notificación al proveedor registrada (simulada)')

                return redirect('ver_evaluacion', evaluacion_id=evaluacion.id)

    # Procesar cambio de estado de flujo de evaluación (solo técnicos y gestores)
    if request.method == 'POST' and (es_gestor or es_tecnico):
        if 'cambiar_estado_flujo' in request.POST:
            nuevo_estado_flujo = request.POST.get('estado_flujo')
            observaciones_flujo = request.POST.get('observaciones_flujo', '')
            puntaje_reevaluacion = request.POST.get('puntaje_reevaluacion', '')
            fecha_reevaluacion = request.POST.get('fecha_reevaluacion', '')

            if nuevo_estado_flujo and nuevo_estado_flujo in dict(Evaluacion.ESTADOS_FLUJO):
                fecha_actual = timezone.now()

                # Agregar fecha automáticamente a las observaciones
                if observaciones_flujo:
                    observaciones_flujo = f"[{fecha_actual.strftime('%d/%m/%Y %H:%M')}] {observaciones_flujo}"
                else:
                    observaciones_flujo = f"[{fecha_actual.strftime('%d/%m/%Y %H:%M')}] Estado de flujo actualizado a {dict(Evaluacion.ESTADOS_FLUJO)[nuevo_estado_flujo]}"

                evaluacion.estado_flujo_evaluacion = nuevo_estado_flujo
                evaluacion.fecha_cambio_estado_flujo = fecha_actual
                evaluacion.observaciones_flujo = observaciones_flujo

                # Si es reevaluación, guardar puntaje y fecha
                if nuevo_estado_flujo == 'REEVALUADO':
                    if puntaje_reevaluacion:
                        evaluacion.puntaje_reevaluacion = int(puntaje_reevaluacion)
                    if fecha_reevaluacion:
                        evaluacion.fecha_reevaluacion = datetime.strptime(fecha_reevaluacion, '%Y-%m-%d').date()

                evaluacion.save()

                messages.success(request, f'Estado de flujo actualizado a: {evaluacion.get_estado_flujo_evaluacion_display()}')
                return redirect('ver_evaluacion', evaluacion_id=evaluacion.id)


    # Procesar abandono del proceso por el proveedor
    if request.method == 'POST' and 'abandonar_proceso' in request.POST:
        motivo_abandono = request.POST.get('motivo_abandono', '').strip()

        # Validar que se pueda rechazar
        if plan and plan.estado in ['PM_RADICADO', 'APROBADO', 'CANCELACION_RADICADA']:
            messages.error(request, 'No se puede abandonar el proceso porque ya está radicado.')
        elif dias_sin_plan > 30:
            messages.error(request, 'No se puede abandonar el proceso porque el plazo de 30 días ya expiró.')
        elif motivo_abandono:
            if not plan:
                # Crear plan en estado RECHAZADO si no existe
                plan = PlanMejoramiento.objects.create(
                    proveedor=proveedor,
                    evaluacion=evaluacion,
                    estado='RECHAZADO',
                    analisis_causa='PROCESO CANCELADO POR EL PROVEEDOR',
                    acciones_propuestas='No aplica - Proceso cancelado',
                    responsable=proveedor.razon_social,
                    fecha_implementacion=date.today(),
                    indicadores_seguimiento='No aplica - Proceso cancelado',
                    comentarios_tecnico=f'PROVEEDOR RECHAZÓ EL PROCESO\n\nMotivo: {motivo_abandono}\n\nFecha: {timezone.now().strftime("%d/%m/%Y %H:%M")}\nProveedor: {proveedor.razon_social}'
                )
                estado_anterior = 'SIN_PLAN'
            else:
                # Cambiar estado del plan existente a RECHAZADO
                estado_anterior = plan.estado
                plan.estado = 'RECHAZADO'
                plan.comentarios_tecnico = f'PROVEEDOR RECHAZÓ EL PROCESO\n\nMotivo: {motivo_abandono}\n\nFecha: {timezone.now().strftime("%d/%m/%Y %H:%M")}\nProveedor: {proveedor.razon_social}'
                plan.save()

            # Crear registro en historial
            HistorialEstado.objects.create(
                plan=plan,
                estado_anterior=estado_anterior,
                estado_nuevo='RECHAZADO',
                usuario=request.user,
                comentario=f'{proveedor.razon_social} decidió no presentar el plan. Motivo: {motivo_abandono}'
            )

            messages.warning(request, 'Ha informado que no presentará el plan de mejoramiento. El técnico será notificado para radicar la cancelación.')
            return redirect('ver_evaluacion', evaluacion_id=evaluacion_id)
        else:
            messages.error(request, 'Debe proporcionar un motivo para no presentar el plan.')

    # Procesar revisión del plan (técnicos y gestores) - Paso 5.1
    if request.method == 'POST' and (es_gestor or es_tecnico) and 'revisar_plan' in request.POST:
        decision = request.POST.get('decision_plan')
        observaciones_plan = request.POST.get('observaciones_plan', '')

        if decision and plan:
            estado_anterior = plan.estado

            if decision == 'APROBAR':
                # Aprobar el plan y enviarlo a radicación
                plan.estado = 'EN_RADICACION'
                plan.revisado_por = request.user
                plan.fecha_revision = timezone.now()
                plan.comentarios_tecnico = observaciones_plan
                plan.save()

                # Crear registro en historial
                tipo_usuario = "Gestor" if es_gestor else "Técnico"
                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior=estado_anterior,
                    estado_nuevo='EN_RADICACION',
                    usuario=request.user,
                    comentario=f'{tipo_usuario} {request.user.get_full_name() or request.user.username} aprobó el plan: {observaciones_plan}'
                )

                messages.success(request, 'Plan aprobado exitosamente. Estado actualizado a "En Radicación"')
                return redirect('ver_evaluacion', evaluacion_id=evaluacion_id)

            elif decision == 'SOLICITAR_AJUSTES':
                # Solicitar ajustes al proveedor
                plan.estado = 'SOLICITUD_AJUSTES'
                plan.revisado_por = request.user
                plan.fecha_revision = timezone.now()
                plan.comentarios_tecnico = observaciones_plan
                plan.save()

                # Crear registro en historial
                tipo_usuario = "Gestor" if es_gestor else "Técnico"
                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior=estado_anterior,
                    estado_nuevo='SOLICITUD_AJUSTES',
                    usuario=request.user,
                    comentario=f'{tipo_usuario} {request.user.get_full_name() or request.user.username} solicitó ajustes: {observaciones_plan}'
                )

                messages.warning(request, 'Se solicitaron ajustes al plan. El proveedor ha sido notificado.')
                return redirect('ver_evaluacion', evaluacion_id=evaluacion_id)

    # Procesar cambio de estado (gestores y técnicos)
    if request.method == 'POST' and (es_gestor or es_tecnico) and plan:
        nuevo_estado = request.POST.get('estado')
        observaciones = request.POST.get('observaciones', '')

        if nuevo_estado and nuevo_estado in dict(PlanMejoramiento.ESTADOS):
            # Guardar estado anterior
            estado_anterior = plan.estado

            # Actualizar estado del plan
            plan.estado = nuevo_estado

            # Actualizar campos según el nuevo estado
            if nuevo_estado == 'EN_REVISION':
                plan.revisado_por = request.user
                plan.fecha_revision = timezone.now()
            elif nuevo_estado == 'APROBADO':
                plan.revisado_por = request.user
                plan.fecha_aprobacion = timezone.now()
                plan.fecha_revision = timezone.now()
            elif nuevo_estado == 'REQUIERE_AJUSTES':
                plan.revisado_por = request.user
                plan.fecha_revision = timezone.now()
            elif nuevo_estado == 'RECHAZADO':
                plan.revisado_por = request.user
                plan.fecha_revision = timezone.now()

            # Guardar observaciones del técnico
            if observaciones:
                plan.comentarios_tecnico = observaciones

            plan.save()

            # Crear registro en historial
            tipo_usuario = "Gestor" if es_gestor else "Técnico"
            comentario_historial = f'{tipo_usuario} {request.user.get_full_name() or request.user.username}: {observaciones}' if observaciones else f'{tipo_usuario} cambió el estado'

            HistorialEstado.objects.create(
                plan=plan,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                usuario=request.user,
                comentario=comentario_historial
            )

            messages.success(request, f'Estado actualizado a: {dict(PlanMejoramiento.ESTADOS)[nuevo_estado]}')
            return redirect('proveedor_ver_evaluacion', evaluacion_id=evaluacion_id)

    # Procesar marcado de "No Recibido" cuando se vence el plazo (técnicos y gestores)
    if request.method == 'POST' and (es_gestor or es_tecnico) and 'marcar_no_recibido' in request.POST:
        observaciones_no_recibido = request.POST.get('observaciones_no_recibido', '')

        # Verificar que el plazo realmente haya vencido
        if evaluacion.fecha_limite_plan:
            dias_vencidos = (timezone.now().date() - evaluacion.fecha_limite_plan).days

            if dias_vencidos >= 0:  # Plazo vencido
                # Crear o actualizar el plan con estado NO_RECIBIDO
                estado_anterior = None
                if not plan:
                    # Crear un plan vacío con estado NO_RECIBIDO
                    info_vencimiento = f"--- PLAN NO RECIBIDO - VENCIMIENTO DEL PLAZO ---\n"
                    info_vencimiento += f"Fecha límite: {evaluacion.fecha_limite_plan.strftime('%d/%m/%Y')}\n"
                    info_vencimiento += f"Días de vencimiento: {dias_vencidos} días\n"
                    info_vencimiento += f"Marcado por: {request.user.get_full_name() or request.user.username}\n"
                    info_vencimiento += f"Fecha de marcado: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n"
                    if observaciones_no_recibido:
                        info_vencimiento += f"Observaciones: {observaciones_no_recibido}\n"

                    plan = PlanMejoramiento.objects.create(
                        evaluacion=evaluacion,
                        proveedor=evaluacion.proveedor,
                        estado='NO_RECIBIDO',
                        comentarios_tecnico=info_vencimiento
                    )
                else:
                    # Actualizar plan existente
                    estado_anterior = plan.estado
                    plan.estado = 'NO_RECIBIDO'

                    # Agregar información del vencimiento
                    info_vencimiento = f"\n\n--- PLAN NO RECIBIDO - VENCIMIENTO DEL PLAZO ---\n"
                    info_vencimiento += f"Fecha límite: {evaluacion.fecha_limite_plan.strftime('%d/%m/%Y')}\n"
                    info_vencimiento += f"Días de vencimiento: {dias_vencidos} días\n"
                    info_vencimiento += f"Marcado por: {request.user.get_full_name() or request.user.username}\n"
                    info_vencimiento += f"Fecha de marcado: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n"
                    if observaciones_no_recibido:
                        info_vencimiento += f"Observaciones: {observaciones_no_recibido}\n"

                    plan.comentarios_tecnico += info_vencimiento
                    plan.save()

                # Crear registro en historial
                tipo_usuario = "Gestor" if es_gestor else "Técnico"
                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior=estado_anterior,
                    estado_nuevo='NO_RECIBIDO',
                    usuario=request.user,
                    comentario=f'{tipo_usuario} {request.user.get_full_name() or request.user.username} marcó el plan como No Recibido por vencimiento del plazo. {observaciones_no_recibido}'
                )

                messages.success(request, 'Plan marcado como No Recibido. El proceso ha finalizado por vencimiento del plazo.')
                return redirect('proveedor_ver_evaluacion', evaluacion_id=evaluacion_id)
            else:
                messages.error(request, 'No se puede marcar como No Recibido porque el plazo aún no ha vencido.')
                return redirect('proveedor_ver_evaluacion', evaluacion_id=evaluacion_id)

    # Procesar radicación de cancelación (técnicos y gestores cuando el plan está RECHAZADO)
    if request.method == 'POST' and (es_gestor or es_tecnico) and 'radicar_cancelacion' in request.POST and plan:
        if plan.estado == 'RECHAZADO':
            estado_anterior = plan.estado
            observaciones_cancelacion = request.POST.get('observaciones_cancelacion', '')

            # Cambiar estado a CANCELACION_RADICADA
            plan.estado = 'CANCELACION_RADICADA'

            # Agregar información de la radicación a los comentarios
            info_radicacion = f"\n\n--- RADICACIÓN DE CANCELACIÓN ---\n"
            info_radicacion += f"Radicada por: {request.user.get_full_name() or request.user.username}\n"
            info_radicacion += f"Fecha de radicación: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n"
            if observaciones_cancelacion:
                info_radicacion += f"Observaciones: {observaciones_cancelacion}\n"

            plan.comentarios_tecnico += info_radicacion
            plan.save()

            # Crear registro en historial
            tipo_usuario = "Gestor" if es_gestor else "Técnico"
            HistorialEstado.objects.create(
                plan=plan,
                estado_anterior=estado_anterior,
                estado_nuevo='CANCELACION_RADICADA',
                usuario=request.user,
                comentario=f'{tipo_usuario} {request.user.get_full_name() or request.user.username} radicó la cancelación. {observaciones_cancelacion}'
            )

            messages.success(request, 'Cancelación radicada exitosamente. El proceso ha finalizado.')
            return redirect('proveedor_ver_evaluacion', evaluacion_id=evaluacion_id)

    # Extraer información del tipo de calificación desde observaciones generales
    tipo_calificacion_nombre = None
    tipo_calificacion_obj = None
    criterios_con_respuestas = []

    if evaluacion.observaciones_generales:
        lineas = evaluacion.observaciones_generales.split('\n')
        for linea in lineas:
            if 'Tipo de Calificación:' in linea:
                tipo_calificacion_nombre = linea.replace('Tipo de Calificación:', '').strip()
                # Buscar el tipo de calificación en la BD
                from .models import TipoCalificacion, RespuestaEvaluacion
                tipo_calificacion_obj = TipoCalificacion.objects.filter(
                    nombre=tipo_calificacion_nombre,
                    activo=True
                ).first()
                break

    # Si encontramos el tipo, cargar las respuestas seleccionadas
    if tipo_calificacion_obj:
        respuestas = RespuestaEvaluacion.objects.filter(
            evaluacion=evaluacion
        ).select_related('criterio').order_by('id_criterio')

        for respuesta in respuestas:
            puntaje_maximo = respuesta.criterio.tipo_calificacion.criterios.filter(
                id_criterio=respuesta.id_criterio
            ).order_by('-puntuacion_maxima').first().puntuacion_maxima if respuesta.criterio.tipo_calificacion.criterios.filter(id_criterio=respuesta.id_criterio).exists() else 0

            # Calcular porcentaje y determinar clases CSS
            porcentaje = (float(respuesta.puntuacion_obtenida) / float(puntaje_maximo) * 100) if puntaje_maximo > 0 else 0

            if porcentaje >= 80:
                clase_fila = 'table-success'
                clase_badge = 'bg-success'
            elif porcentaje >= 60:
                clase_fila = 'table-warning'
                clase_badge = 'bg-warning text-dark'
            else:
                clase_fila = 'table-danger'
                clase_badge = 'bg-danger'

            criterios_con_respuestas.append({
                'id_criterio': respuesta.id_criterio,
                'descripcion': respuesta.criterio.descripcion_criterio,
                'puntaje_obtenido': respuesta.puntuacion_obtenida,
                'puntaje_maximo': puntaje_maximo,
                'respuesta_seleccionada': respuesta.criterio.respuesta_corta or respuesta.criterio.respuesta_normal,
                'observaciones': respuesta.observaciones,
                'clase_fila': clase_fila,
                'clase_badge': clase_badge
            })

    # Calcular días restantes y porcentaje (dias_sin_plan ya fue calculado al inicio)
    dias_restantes = max(0, 30 - dias_sin_plan)
    porcentaje_transcurrido = min(100, int((dias_sin_plan / 30) * 100)) if dias_sin_plan > 0 else 0

    # Crear automáticamente un plan en estado BORRADOR si no existe
    # Solo se crea después de seleccionar la ruta Y solo si:
    # - Es FLUJO_NORMAL, o
    # - Es REEVALUADO y el puntaje de reevaluación es < 80
    # NO se crea si está en ACLARACION (esperando reevaluación)
    if (not plan and
        evaluacion.fecha_cambio_estado_flujo and
        (evaluacion.estado_flujo_evaluacion == 'FLUJO_NORMAL' or
         (evaluacion.estado_flujo_evaluacion == 'REEVALUADO' and evaluacion.puntaje_reevaluacion and evaluacion.puntaje_reevaluacion < 80))):
        # Crear el plan automáticamente con fecha de implementación por defecto (30 días desde hoy)
        fecha_implementacion_default = date.today() + timedelta(days=30)
        plan = PlanMejoramiento.objects.create(
            evaluacion=evaluacion,
            proveedor=evaluacion.proveedor,
            estado='BORRADOR',
            fecha_creacion=timezone.now(),
            fecha_implementacion=fecha_implementacion_default
        )
        messages.info(request, 'Se ha creado automáticamente un plan de mejoramiento en estado BORRADOR para que el proveedor pueda completarlo.')

    # Contar iteraciones de revisión (cuántas veces se ha solicitado ajustes)
    num_iteraciones_revision = 0
    historial_revision_plan = []
    if plan:
        num_iteraciones_revision = HistorialEstado.objects.filter(
            plan=plan,
            estado_nuevo='SOLICITUD_AJUSTES'
        ).count()

        # Obtener historial completo de revisión del plan
        historial_revision_plan = HistorialEstado.objects.filter(
            plan=plan,
            estado_nuevo__in=['ENVIADO', 'PM_REEVALUADO', 'SOLICITUD_AJUSTES', 'EN_RADICACION']
        ).order_by('fecha_cambio')

    context = {
        'evaluacion': evaluacion,
        'plan': plan,
        'requiere_plan': evaluacion.puntaje < 80,
        'es_gestor': es_gestor,
        'es_tecnico': es_tecnico,
        'es_proveedor': es_proveedor,
        'estados_plan': PlanMejoramiento.ESTADOS,
        'estados_firma': Evaluacion.ESTADOS_FIRMA,
        'estados_flujo': Evaluacion.ESTADOS_FLUJO,
        'tipo_calificacion_nombre': tipo_calificacion_nombre,
        'criterios_con_respuestas': criterios_con_respuestas,
        'dias_sin_plan': dias_sin_plan,
        'dias_transcurridos': dias_sin_plan,
        'dias_restantes': dias_restantes,
        'porcentaje_transcurrido': porcentaje_transcurrido,
        'num_iteraciones_revision': num_iteraciones_revision,
        'historial_revision_plan': historial_revision_plan,
    }

    return render(request, 'planes/ver_evaluacion.html', context)


@login_required
def crear_plan(request):
    """Vista para crear un nuevo plan de mejoramiento"""
    try:
        proveedor = request.user.proveedor
    except:
        messages.error(request, 'No tiene permisos de proveedor')
        return redirect('login')
    
    # Obtener la evaluación más reciente que requiere plan
    evaluacion = Evaluacion.objects.filter(
        proveedor=proveedor,
        puntaje__lt=80
    ).order_by('-fecha').first()
    
    if not evaluacion:
        messages.warning(request, 'No tiene evaluaciones que requieran plan de mejoramiento')
        return redirect('proveedor_dashboard')
    
    # Verificar si ya existe un plan para esta evaluación
    plan_existente = PlanMejoramiento.objects.filter(
        proveedor=proveedor,
        evaluacion=evaluacion
    ).first()
    
    if plan_existente and plan_existente.estado != 'RECHAZADO':
        messages.info(request, 'Ya existe un plan para esta evaluación')
        return redirect('proveedor_ver_plan', plan_id=plan_existente.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validar datos requeridos antes de crear el plan
                fecha_impl = request.POST.get('fecha_implementacion')
                if not fecha_impl:
                    messages.error(request, 'La fecha de implementación es requerida')
                    return render(request, 'planes/crear_plan.html', {
                        'evaluacion': evaluacion,
                        'proveedor': proveedor,
                        'form_data': request.POST  # Preservar datos del formulario
                    })
                
                # Crear el plan dentro de la transacción
                plan = PlanMejoramiento.objects.create(
                    evaluacion=evaluacion,
                    proveedor=proveedor,
                    analisis_causa=request.POST.get('analisis_causa', ''),
                    acciones_propuestas=request.POST.get('acciones_propuestas', ''),
                    responsable=request.POST.get('responsable', ''),
                    fecha_implementacion=fecha_impl,
                    indicadores_seguimiento=request.POST.get('indicadores', ''),
                    estado='ENVIADO',
                    fecha_envio=timezone.now()
                )
                
                # Procesar acciones individuales
                contador = 1
                while f'accion_{contador}' in request.POST:
                    if request.POST.get(f'accion_{contador}'):
                        fecha_comp = request.POST.get(f'fecha_{contador}')
                        if fecha_comp:  # Solo crear si hay fecha
                            AccionMejora.objects.create(
                                plan=plan,
                                descripcion=request.POST.get(f'accion_{contador}'),
                                responsable=request.POST.get(f'responsable_{contador}', ''),
                                fecha_compromiso=fecha_comp,
                                indicador=request.POST.get(f'indicador_{contador}', '')
                            )
                    contador += 1
                
                # Procesar archivos adjuntos
                contador = 1
                while f'archivo_{contador}' in request.FILES:
                    archivo = request.FILES.get(f'archivo_{contador}')
                    tipo_doc = request.POST.get(f'tipo_documento_{contador}', 'OTRO')
                    descripcion = request.POST.get(f'descripcion_{contador}', '')

                    if archivo:
                        from planes.models import PlanAdjunto
                        PlanAdjunto.objects.create(
                            plan=plan,
                            tipo_documento=tipo_doc,
                            archivo=archivo,
                            nombre_original=archivo.name,
                            descripcion=descripcion,
                            subido_por=request.user
                        )
                    contador += 1
                
                # Registrar en historial
                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior='BORRADOR',
                    estado_nuevo='ENVIADO',
                    usuario=request.user,
                    comentario='Plan creado y enviado para revisión'
                )
                
                messages.success(request, 'Plan de mejoramiento enviado exitosamente')
                return redirect('proveedor_ver_plan', plan_id=plan.id)
                
        except Exception as e:
            messages.error(request, f'Error al crear el plan: {str(e)}')
            # Retornar el formulario con los datos ingresados para no perderlos
            return render(request, 'planes/crear_plan.html', {
                'evaluacion': evaluacion,
                'proveedor': proveedor,
                'form_data': request.POST
            })
    
    context = {
        'evaluacion': evaluacion,
        'proveedor': proveedor,
    }
    
    return render(request, 'planes/crear_plan.html', context)


@login_required
def ver_plan(request, plan_id):
    """Vista para ver y editar el detalle de un plan"""
    # Verificar si es proveedor
    es_proveedor = hasattr(request.user, 'proveedor')

    if es_proveedor:
        # Si es proveedor, solo puede ver sus propios planes
        proveedor = request.user.proveedor
        plan = get_object_or_404(
            PlanMejoramiento,
            id=plan_id,
            proveedor=proveedor
        )
        # Determinar si el proveedor puede editar
        puede_editar = plan.estado in ['BORRADOR', 'REQUIERE_AJUSTES', 'SOLICITUD_AJUSTES']
        # Determinar si puede agregar archivos adjuntos (más permisivo)
        puede_adjuntar = plan.estado not in ['APROBADO', 'RECHAZADO']
        es_gestor = False
        es_tecnico = False
    else:
        # Si es técnico o gestor, puede ver cualquier plan
        plan = get_object_or_404(PlanMejoramiento, id=plan_id)
        proveedor = plan.proveedor
        # Verificar si es gestor o técnico
        es_gestor = hasattr(request.user, 'perfil') and request.user.perfil.es_gestor
        es_tecnico = hasattr(request.user, 'perfil') and request.user.perfil.es_tecnico
        # Administradores pueden editar planes en BORRADOR y SOLICITUD_AJUSTES
        puede_editar = plan.estado in ['BORRADOR', 'REQUIERE_AJUSTES', 'SOLICITUD_AJUSTES']
        puede_adjuntar = plan.estado not in ['APROBADO', 'RECHAZADO']

    # Manejar POST
    if request.method == 'POST':

        # Si el proveedor rechaza el plan (no desea continuar)
        if es_proveedor and 'rechazar_plan' in request.POST:
            motivo_rechazo = request.POST.get('motivo_rechazo', '')

            if motivo_rechazo:
                estado_anterior = plan.estado
                plan.estado = 'RECHAZADO'
                plan.comentarios_tecnico = f'PROVEEDOR RECHAZÓ EL PROCESO\n\nMotivo: {motivo_rechazo}\n\nFecha: {timezone.now().strftime("%d/%m/%Y %H:%M")}'
                plan.save()

                # Crear registro en historial
                from planes.models import HistorialEstado
                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior=estado_anterior,
                    estado_nuevo='RECHAZADO',
                    usuario=request.user,
                    comentario=f'{proveedor.razon_social} rechazó el proceso. Motivo: {motivo_rechazo}'
                )

                messages.warning(request, 'Ha rechazado el proceso de mejoramiento. El técnico será notificado para radicar la cancelación.')
                return redirect('ver_plan', plan_id=plan.id)
            else:
                messages.error(request, 'Debe proporcionar un motivo para rechazar el plan.')

        # Si el técnico radica la cancelación
        if (es_tecnico or es_gestor) and 'radicar_cancelacion' in request.POST:
            observaciones_cancelacion = request.POST.get('observaciones_cancelacion', '')

            if plan.estado == 'RECHAZADO':
                estado_anterior = plan.estado
                plan.estado = 'CANCELACION_RADICADA'
                if observaciones_cancelacion:
                    plan.comentarios_tecnico += f'\n\nRADICACIÓN DE CANCELACIÓN\nObservaciones del técnico: {observaciones_cancelacion}\nFecha: {timezone.now().strftime("%d/%m/%Y %H:%M")}'
                plan.save()

                # Crear registro en historial
                from planes.models import HistorialEstado
                tipo_usuario = "Gestor" if es_gestor else "Técnico"
                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior=estado_anterior,
                    estado_nuevo='CANCELACION_RADICADA',
                    usuario=request.user,
                    comentario=f'{tipo_usuario} {request.user.get_full_name() or request.user.username} radicó la cancelación del proceso. {observaciones_cancelacion}'
                )

                messages.success(request, 'Cancelación radicada exitosamente. El proceso ha finalizado.')
                return redirect('ver_plan', plan_id=plan.id)

        # Si es técnico o gestor, procesar revisión
        if (es_tecnico or es_gestor) and 'accion_revision' in request.POST:
            nuevo_estado = request.POST.get('estado')
            observaciones = request.POST.get('observaciones', '')

            if nuevo_estado and nuevo_estado in dict(PlanMejoramiento.ESTADOS):
                # Guardar estado anterior
                estado_anterior = plan.estado

                # Actualizar estado del plan
                plan.estado = nuevo_estado

                # Actualizar campos según el nuevo estado
                if nuevo_estado == 'EN_REVISION':
                    plan.revisado_por = request.user
                    plan.fecha_revision = timezone.now()
                elif nuevo_estado == 'APROBADO':
                    plan.revisado_por = request.user
                    plan.fecha_aprobacion = timezone.now()
                    plan.fecha_revision = timezone.now()
                elif nuevo_estado == 'REQUIERE_AJUSTES':
                    plan.revisado_por = request.user
                    plan.fecha_revision = timezone.now()
                elif nuevo_estado == 'RECHAZADO':
                    plan.revisado_por = request.user
                    plan.fecha_revision = timezone.now()

                # Guardar observaciones del técnico
                if observaciones:
                    plan.comentarios_tecnico = observaciones

                plan.save()

                # Crear registro en historial
                tipo_usuario = "Gestor" if es_gestor else "Técnico"
                comentario_historial = f'{tipo_usuario} {request.user.get_full_name() or request.user.username}: {observaciones}' if observaciones else f'{tipo_usuario} cambió el estado'

                from planes.models import HistorialEstado
                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    usuario=request.user,
                    comentario=comentario_historial
                )

                messages.success(request, f'Estado actualizado a: {dict(PlanMejoramiento.ESTADOS)[nuevo_estado]}')
                return redirect('ver_plan', plan_id=plan.id)

        # Si es proveedor, técnico o gestor, actualizar el plan
        elif es_proveedor or es_tecnico or es_gestor:
            # Guardar estado anterior para notificaciones
            estado_anterior = plan.estado

            # Solo actualizar campos del plan si puede editar
            if puede_editar:
                # Importar modelo de historial de cambios
                from planes.models import HistorialCambioCampo

                # Diccionario de campos a rastrear
                campos_rastrear = {
                    'analisis_causa': 'Análisis de Causa Raíz',
                    'acciones_propuestas': 'Acciones Propuestas',
                    'responsable': 'Responsable',
                    'indicadores_seguimiento': 'Indicadores de Seguimiento',
                }

                # Registrar cambios en los campos
                for campo_db, campo_nombre in campos_rastrear.items():
                    valor_anterior = getattr(plan, campo_db, '') or ''
                    valor_nuevo = request.POST.get(campo_db, '')

                    # Solo registrar si hubo cambio
                    if valor_anterior != valor_nuevo:
                        HistorialCambioCampo.objects.create(
                            plan=plan,
                            campo=campo_nombre,
                            valor_anterior=valor_anterior,
                            valor_nuevo=valor_nuevo,
                            usuario=request.user
                        )

                # Fecha de implementación
                fecha_impl = request.POST.get('fecha_implementacion')
                if fecha_impl:
                    fecha_nueva = datetime.strptime(fecha_impl, '%Y-%m-%d').date()
                    if plan.fecha_implementacion != fecha_nueva:
                        HistorialCambioCampo.objects.create(
                            plan=plan,
                            campo='Fecha de Implementación',
                            valor_anterior=str(plan.fecha_implementacion) if plan.fecha_implementacion else '',
                            valor_nuevo=str(fecha_nueva),
                            usuario=request.user
                        )
                        plan.fecha_implementacion = fecha_nueva

                # Actualizar campos
                plan.analisis_causa = request.POST.get('analisis_causa', '')
                plan.acciones_propuestas = request.POST.get('acciones_propuestas', '')
                plan.responsable = request.POST.get('responsable', '')
                plan.indicadores_seguimiento = request.POST.get('indicadores_seguimiento', '')

                # Cambiar estado automáticamente (proveedor o durante pruebas)
                # TODO: A futuro, cambiar solo cuando es_proveedor = True
                if plan.estado == 'BORRADOR':
                    plan.estado = 'ENVIADO'
                    plan.fecha_envio = timezone.now()
                elif plan.estado == 'SOLICITUD_AJUSTES':
                    # Si se hacen ajustes, cambiar a PM Reevaluado
                    plan.estado = 'PM_REEVALUADO'
                    plan.fecha_envio = timezone.now()

                plan.save()

                # Crear notificación para el técnico
                if es_proveedor:
                    from planes.models import Notificacion
                    # Obtener el técnico asignado a la evaluación
                    if plan.evaluacion.tecnico_asignado:
                        if estado_anterior == 'BORRADOR' and plan.estado == 'ENVIADO':
                            Notificacion.objects.create(
                                usuario=plan.evaluacion.tecnico_asignado,
                                tipo='PLAN_ENVIADO',
                                plan=plan,
                                mensaje=f'El proveedor {proveedor.razon_social} ha enviado el plan de mejoramiento para revisión.'
                            )
                        elif estado_anterior == 'SOLICITUD_AJUSTES' and plan.estado == 'PM_REEVALUADO':
                            Notificacion.objects.create(
                                usuario=plan.evaluacion.tecnico_asignado,
                                tipo='PLAN_REEVALUADO',
                                plan=plan,
                                mensaje=f'El proveedor {proveedor.razon_social} ha reenviado el plan de mejoramiento con los ajustes solicitados.'
                            )

            # Procesar archivos adjuntos (si puede adjuntar)
            archivos_subidos = 0
            if puede_adjuntar:
                contador = 1
                while f'archivo_{contador}' in request.FILES:
                    archivo = request.FILES.get(f'archivo_{contador}')
                    tipo_doc = request.POST.get(f'tipo_documento_{contador}', 'OTRO')
                    descripcion = request.POST.get(f'descripcion_{contador}', '')

                    if archivo:
                        from planes.models import PlanAdjunto
                        PlanAdjunto.objects.create(
                            plan=plan,
                            tipo_documento=tipo_doc,
                            archivo=archivo,
                            nombre_original=archivo.name,
                            descripcion=descripcion,
                            subido_por=request.user
                        )
                        archivos_subidos += 1
                    contador += 1

            # Registrar en historial si hubo cambios
            if puede_editar or archivos_subidos > 0:
                try:
                    from planes.models import HistorialEstado
                    if es_proveedor:
                        comentario = f'Plan modificado por {proveedor.razon_social}'
                        if archivos_subidos > 0 and not puede_editar:
                            comentario = f'{proveedor.razon_social} agregó {archivos_subidos} archivo(s) adjunto(s)'
                    else:
                        tipo_usuario = "Gestor" if es_gestor else "Técnico"
                        comentario = f'{tipo_usuario} {request.user.get_full_name() or request.user.username} modificó el plan'
                        if archivos_subidos > 0 and not puede_editar:
                            comentario = f'{tipo_usuario} agregó {archivos_subidos} archivo(s) adjunto(s)'

                    # Mejorar el comentario si hubo cambio de estado
                    if estado_anterior == 'BORRADOR' and plan.estado == 'ENVIADO':
                        comentario = f'{proveedor.razon_social} envió el plan de mejoramiento para revisión'
                    elif estado_anterior == 'SOLICITUD_AJUSTES' and plan.estado == 'PM_REEVALUADO':
                        comentario = f'{proveedor.razon_social} corrigió y reenvió el plan de mejoramiento'

                    HistorialEstado.objects.create(
                        plan=plan,
                        estado_anterior=estado_anterior,
                        estado_nuevo=plan.estado,
                        usuario=request.user,
                        comentario=comentario
                    )
                except:
                    pass

            # Mensajes y redirección según el cambio de estado
            if puede_editar:
                if estado_anterior == 'BORRADOR' and plan.estado == 'ENVIADO':
                    messages.success(request, 'Plan enviado exitosamente para revisión del técnico')
                    # Redirigir a la evaluación para ver el estado actualizado
                    return redirect('ver_evaluacion', evaluacion_id=plan.evaluacion.id)
                elif estado_anterior == 'SOLICITUD_AJUSTES' and plan.estado == 'PM_REEVALUADO':
                    messages.success(request, 'Plan corregido y reenviado exitosamente. El técnico revisará los ajustes realizados.')
                    # Redirigir a la evaluación para ver el estado actualizado
                    return redirect('ver_evaluacion', evaluacion_id=plan.evaluacion.id)
                else:
                    messages.success(request, 'Plan actualizado exitosamente')
            elif archivos_subidos > 0:
                messages.success(request, f'Se agregaron {archivos_subidos} archivo(s) adjunto(s) exitosamente')

            return redirect('ver_plan', plan_id=plan.id)

    context = {
        'plan': plan,
        'puede_editar': puede_editar,
        'puede_adjuntar': puede_adjuntar,
        'es_proveedor': es_proveedor,
        'es_gestor': es_gestor,
        'es_tecnico': es_tecnico,
        'estados_plan': PlanMejoramiento.ESTADOS,
        'acciones': plan.acciones.all(),
        'documentos': plan.documentos.all(),
        'historial': plan.historial.all()[:5],
        'historial_cambios_campos': plan.historial_cambios_campos.all()[:20],
    }

    return render(request, 'planes/ver_plan.html', context)


@login_required
def editar_plan(request, plan_id):
    """Vista para editar un plan cuando requiere ajustes"""
    try:
        proveedor = request.user.proveedor
        plan = get_object_or_404(
            PlanMejoramiento,
            id=plan_id,
            proveedor=proveedor,
            estado__in=['BORRADOR', 'REQUIERE_AJUSTES', 'FIRMADO_ENVIADO']
        )
    except:
        messages.error(request, 'No puede editar este plan')
        return redirect('proveedor_dashboard')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Guardar estado anterior
                estado_anterior = plan.estado
                
                # Validar fecha de implementación
                fecha_impl = request.POST.get('fecha_implementacion', plan.fecha_implementacion)
                if not fecha_impl:
                    messages.error(request, 'La fecha de implementación es requerida')
                    return render(request, 'planes/editar_plan.html', {
                        'plan': plan,
                        'acciones': plan.acciones.all(),
                        'form_data': request.POST
                    })
                
                # Actualizar el plan dentro de la transacción
                plan.analisis_causa = request.POST.get('analisis_causa', plan.analisis_causa)
                plan.acciones_propuestas = request.POST.get('acciones_propuestas', plan.acciones_propuestas)
                plan.responsable = request.POST.get('responsable', plan.responsable)
                plan.fecha_implementacion = fecha_impl
                plan.indicadores_seguimiento = request.POST.get('indicadores', plan.indicadores_seguimiento)

                # Cambiar estado a ENVIADO y registrar fecha
                plan.estado = 'ENVIADO'
                plan.fecha_envio = timezone.now()

                # Solo incrementar versión si ya estaba enviado antes (reenvío)
                if estado_anterior in ['REQUIERE_AJUSTES', 'FIRMADO_ENVIADO']:
                    plan.numero_version += 1

                # Procesar archivos adjuntos específicos
                if 'archivo_analisis_causa' in request.FILES:
                    plan.archivo_analisis_causa = request.FILES['archivo_analisis_causa']

                if 'archivo_acciones_propuestas' in request.FILES:
                    plan.archivo_acciones_propuestas = request.FILES['archivo_acciones_propuestas']

                if 'archivo_indicadores' in request.FILES:
                    plan.archivo_indicadores = request.FILES['archivo_indicadores']

                if 'archivo_otros' in request.FILES:
                    plan.archivo_otros = request.FILES['archivo_otros']

                plan.save()
                
                # Actualizar acciones
                plan.acciones.all().delete()  # Eliminar acciones anteriores
                contador = 1
                while f'accion_{contador}' in request.POST:
                    if request.POST.get(f'accion_{contador}'):
                        fecha_comp = request.POST.get(f'fecha_{contador}')
                        if fecha_comp:  # Solo crear si hay fecha
                            AccionMejora.objects.create(
                                plan=plan,
                                descripcion=request.POST.get(f'accion_{contador}'),
                                responsable=request.POST.get(f'responsable_{contador}', ''),
                                fecha_compromiso=fecha_comp,
                                indicador=request.POST.get(f'indicador_{contador}', '')
                            )
                    contador += 1
                
                # Procesar nuevos archivos adjuntos
                contador = 1
                while f'archivo_{contador}' in request.FILES:
                    archivo = request.FILES.get(f'archivo_{contador}')
                    tipo_doc = request.POST.get(f'tipo_documento_{contador}', 'OTRO')
                    descripcion = request.POST.get(f'descripcion_{contador}', '')

                    if archivo:
                        from planes.models import PlanAdjunto
                        PlanAdjunto.objects.create(
                            plan=plan,
                            tipo_documento=tipo_doc,
                            archivo=archivo,
                            nombre_original=archivo.name,
                            descripcion=descripcion,
                            subido_por=request.user
                        )
                    contador += 1
                
                # Registrar en historial
                if estado_anterior == 'BORRADOR':
                    comentario_historial = 'Plan enviado para revisión por primera vez'
                    mensaje_exito = 'Plan enviado exitosamente. El sistema ha actualizado el estado a "ENVIADO" y el técnico será notificado para su revisión.'
                else:
                    comentario_historial = 'Plan ajustado y reenviado para revisión'
                    mensaje_exito = 'Plan actualizado y reenviado exitosamente'

                HistorialEstado.objects.create(
                    plan=plan,
                    estado_anterior=estado_anterior,
                    estado_nuevo='ENVIADO',
                    usuario=request.user,
                    comentario=comentario_historial
                )

                messages.success(request, mensaje_exito)
                return redirect('proveedor_ver_plan', plan_id=plan.id)
                
        except Exception as e:
            messages.error(request, f'Error al actualizar el plan: {str(e)}')
            return render(request, 'planes/editar_plan.html', {
                'plan': plan,
                'acciones': plan.acciones.all(),
                'form_data': request.POST
            })
    
    context = {
        'plan': plan,
        'acciones': plan.acciones.all(),
        'documentos': plan.documentos.all(),
    }
    
    return render(request, 'planes/editar_plan.html', context)


# ============= VISTAS DEL TÉCNICO =============

@login_required
def panel_tecnico(request):
    """Panel principal para técnicos"""
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos de técnico')
        return redirect('proveedor_dashboard')

    # Obtener todas las evaluaciones
    evaluaciones = Evaluacion.objects.all().select_related('proveedor')

    # Aplicar filtros
    filtro_proveedor = request.GET.get('proveedor', '')
    filtro_fecha_desde = request.GET.get('fecha_desde', '')
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '')
    filtro_categoria = request.GET.get('categoria', '')
    filtro_contrato = request.GET.get('contrato', '')

    if filtro_proveedor:
        evaluaciones = evaluaciones.filter(
            Q(proveedor__razon_social__icontains=filtro_proveedor) |
            Q(proveedor__nit__icontains=filtro_proveedor)
        )

    if filtro_fecha_desde:
        evaluaciones = evaluaciones.filter(fecha__gte=filtro_fecha_desde)

    if filtro_fecha_hasta:
        evaluaciones = evaluaciones.filter(fecha__lte=filtro_fecha_hasta)

    if filtro_categoria:
        if filtro_categoria == 'satisfactoria':
            evaluaciones = evaluaciones.filter(puntaje__gte=80)
        elif filtro_categoria == 'aceptable':
            evaluaciones = evaluaciones.filter(puntaje__gte=60, puntaje__lt=80)
        elif filtro_categoria == 'critica':
            evaluaciones = evaluaciones.filter(puntaje__lt=60)

    if filtro_contrato:
        evaluaciones = evaluaciones.filter(numero_contrato__icontains=filtro_contrato)

    evaluaciones = evaluaciones.order_by('fecha')

    # Estadísticas generales (sin filtros)
    todas_evaluaciones = Evaluacion.objects.all()
    total_evaluaciones = todas_evaluaciones.count()
    promedio_puntaje = todas_evaluaciones.aggregate(Avg('puntaje'))['puntaje__avg'] or 0

    # Obtener todos los planes
    planes = PlanMejoramiento.objects.all().select_related('proveedor', 'evaluacion')

    # Aplicar filtros a planes
    filtro_plan_proveedor = request.GET.get('plan_proveedor', '')
    filtro_plan_estado = request.GET.get('plan_estado', '')
    filtro_plan_fecha_desde = request.GET.get('plan_fecha_desde', '')
    filtro_plan_fecha_hasta = request.GET.get('plan_fecha_hasta', '')

    if filtro_plan_proveedor:
        planes = planes.filter(
            Q(proveedor__razon_social__icontains=filtro_plan_proveedor) |
            Q(proveedor__nit__icontains=filtro_plan_proveedor)
        )

    if filtro_plan_estado:
        planes = planes.filter(estado=filtro_plan_estado)

    if filtro_plan_fecha_desde:
        planes = planes.filter(fecha_creacion__gte=filtro_plan_fecha_desde)

    if filtro_plan_fecha_hasta:
        planes = planes.filter(fecha_creacion__lte=filtro_plan_fecha_hasta)

    planes = planes.order_by('fecha_creacion')

    # Total de planes sin filtros
    todos_planes = PlanMejoramiento.objects.all()
    total_planes = todos_planes.count()

    # Planes por estado (sin filtros)
    planes_borrador = todos_planes.filter(estado='BORRADOR').count()
    planes_enviados = todos_planes.filter(estado='ENVIADO').count()
    planes_revision = todos_planes.filter(estado__in=['EN_REVISION', 'ESPERANDO_APROBACION']).count()
    planes_requiere_ajustes = todos_planes.filter(estado='REQUIERE_AJUSTES').count()
    planes_aprobados = todos_planes.filter(estado='APROBADO').count()
    planes_rechazados = todos_planes.filter(estado='RECHAZADO').count()

    # Evaluaciones por categoría de puntaje
    # Solo evaluaciones que requieren plan de mejoramiento (puntaje < 80)
    evaluaciones_satisfactorias = 0  # No se cargan al sistema
    evaluaciones_aceptables = todas_evaluaciones.filter(puntaje__gte=60, puntaje__lt=80).count()
    evaluaciones_criticas = todas_evaluaciones.filter(puntaje__lt=60).count()

    context = {
        'evaluaciones': evaluaciones,
        'planes': planes,
        'filtros': {
            'proveedor': filtro_proveedor,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
            'categoria': filtro_categoria,
            'contrato': filtro_contrato,
        },
        'filtros_planes': {
            'proveedor': filtro_plan_proveedor,
            'estado': filtro_plan_estado,
            'fecha_desde': filtro_plan_fecha_desde,
            'fecha_hasta': filtro_plan_fecha_hasta,
        },
        'estadisticas': {
            'total_evaluaciones': total_evaluaciones,
            'promedio_puntaje': round(promedio_puntaje, 1),
            'total_planes': total_planes,
            'planes_borrador': planes_borrador,
            'planes_enviados': planes_enviados,
            'planes_revision': planes_revision,
            'planes_requiere_ajustes': planes_requiere_ajustes,
            'planes_aprobados': planes_aprobados,
            'planes_rechazados': planes_rechazados,
            'evaluaciones_satisfactorias': evaluaciones_satisfactorias,
            'evaluaciones_aceptables': evaluaciones_aceptables,
            'evaluaciones_criticas': evaluaciones_criticas,
        }
    }

    return render(request, 'planes/panel_tecnico.html', context)


@login_required
def revisar_plan(request, plan_id):
    """Vista para revisar un plan específico"""
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos de técnico')
        return redirect('proveedor_dashboard')
    
    plan = get_object_or_404(PlanMejoramiento, id=plan_id)
    
    # Solo cambiar a en revisión si está enviado (no si ya está aprobado/rechazado)
    if plan.estado == 'ENVIADO':
        plan.estado = 'EN_REVISION'
        plan.save()
    
    # Si el plan ya está decidido, solo mostrar en modo lectura
    es_modo_lectura = plan.estado in ['APROBADO', 'RECHAZADO']
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        comentarios = request.POST.get('comentarios', '')
        
        estado_anterior = plan.estado
        
        # Actualizar el plan
        plan.estado = decision
        plan.comentarios_tecnico = comentarios
        plan.fecha_revision = timezone.now()
        plan.revisado_por = request.user
        
        if decision == 'APROBADO':
            plan.fecha_aprobacion = timezone.now()
        
        plan.save()
        
        # Registrar en historial
        HistorialEstado.objects.create(
            plan=plan,
            estado_anterior=estado_anterior,
            estado_nuevo=decision,
            usuario=request.user,
            comentario=comentarios
        )
        
        # Mensaje según decisión
        if decision == 'APROBADO':
            messages.success(request, 'Plan aprobado exitosamente')
        elif decision == 'REQUIERE_AJUSTES':
            messages.warning(request, 'Se han solicitado ajustes al proveedor')
        elif decision == 'RECHAZADO':
            messages.error(request, 'Plan rechazado')
        
        return redirect('tecnico_panel')
    
    # Obtener historial de evaluaciones del proveedor
    evaluaciones_historico = Evaluacion.objects.filter(
        proveedor=plan.proveedor
    ).order_by('fecha')[:3]
    
    context = {
        'plan': plan,
        'acciones': plan.acciones.all(),
        'documentos': plan.documentos.all(),
        'historial': plan.historial.all()[:5],
        'evaluaciones_historico': evaluaciones_historico,
        'es_modo_lectura': es_modo_lectura,
    }
    
    return render(request, 'planes/revisar_plan.html', context)


@login_required
def crear_evaluacion(request, proveedor_id=None):
    """Vista para crear evaluaciones de proveedores"""
    # Verificar que NO sea proveedor (es decir, es técnico o admin)
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'Los proveedores no pueden crear evaluaciones')
        return redirect('proveedor_dashboard')
    
    proveedor = None
    if proveedor_id:
        proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        proveedor_id = request.POST.get('proveedor')
        proveedor = get_object_or_404(Proveedor, id=proveedor_id)
        
        # Obtener puntajes de los nuevos campos
        puntaje_gestion = int(request.POST.get('puntaje_gestion', 0))
        puntaje_calidad = int(request.POST.get('puntaje_calidad', 0))
        puntaje_oportunidad = int(request.POST.get('puntaje_oportunidad', 0))
        puntaje_ambiental_social = int(request.POST.get('puntaje_ambiental_social', 0))
        puntaje_sst = int(request.POST.get('puntaje_sst', 0))
        
        # Calcular puntaje total
        puntaje_total = puntaje_gestion + puntaje_calidad + puntaje_oportunidad + puntaje_ambiental_social + puntaje_sst
        
        # Crear evaluación con los nuevos campos
        evaluacion = Evaluacion.objects.create(
            proveedor=proveedor,
            periodo=request.POST.get('periodo'),
            numero_contrato=request.POST.get('numero_contrato', ''),
            subcategoria=request.POST.get('subcategoria', ''),
            tecnico_asignado=request.user if hasattr(request.user, 'perfil') and request.user.perfil.tipo_perfil == 'TECNICO' else None,
            puntaje=puntaje_total,
            fecha=request.POST.get('fecha'),
            fecha_limite_aclaracion=request.POST.get('fecha_limite_aclaracion') or None,
            fecha_limite_plan=request.POST.get('fecha_limite_plan') or None,
            # Puntajes por criterio
            puntaje_gestion=puntaje_gestion,
            puntaje_calidad=puntaje_calidad,
            puntaje_oportunidad=puntaje_oportunidad,
            puntaje_ambiental_social=puntaje_ambiental_social,
            puntaje_sst=puntaje_sst,
            # Máximos por criterio (usando valores por defecto)
            max_gestion=int(request.POST.get('max_gestion', 25)),
            max_calidad=int(request.POST.get('max_calidad', 25)),
            max_oportunidad=int(request.POST.get('max_oportunidad', 25)),
            max_ambiental_social=int(request.POST.get('max_ambiental_social', 25)),
            max_sst=int(request.POST.get('max_sst', 25)),
            # Campos de aprobación
            requiere_aprobacion_sst=request.POST.get('requiere_aprobacion_sst') == 'on',
            requiere_aprobacion_ambiental=request.POST.get('requiere_aprobacion_ambiental') == 'on',
            # Observaciones
            observaciones_gestion=request.POST.get('observaciones_gestion', ''),
            observaciones_calidad=request.POST.get('observaciones_calidad', ''),
            observaciones_oportunidad=request.POST.get('observaciones_oportunidad', ''),
            observaciones_ambiental_social=request.POST.get('observaciones_ambiental_social', ''),
            observaciones_sst=request.POST.get('observaciones_sst', ''),
            observaciones_generales=request.POST.get('observaciones', ''),
            observaciones=request.POST.get('observaciones', '')
        )
        
        messages.success(request, f'Evaluación creada exitosamente. Puntaje: {puntaje_total}')

        # Si el puntaje es bajo, notificar al proveedor (Parametrización ITCO-ISA)
        if puntaje_total < 80:
            messages.info(request, f'El proveedor {proveedor.razon_social} debe crear un plan de mejoramiento')
        
        return redirect('tecnico_panel')
    
    # Obtener lista de proveedores
    proveedores = Proveedor.objects.filter(activo=True).order_by('razon_social')
    
    context = {
        'proveedores': proveedores,
        'proveedor_seleccionado': proveedor,
        'periodos': [
            '2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4',
            '2025-Q1', '2025-Q2', '2025-Q3', '2025-Q4'
        ],
        'fecha_hoy': timezone.now().date()
    }
    
    return render(request, 'planes/crear_evaluacion.html', context)


@login_required
def lista_proveedores(request):
    """Vista para ver todos los proveedores y sus estados"""
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos de técnico')
        return redirect('proveedor_dashboard')
    
    # Construir lista de proveedores con sus evaluaciones y planes
    proveedores_lista = []
    
    proveedores = Proveedor.objects.all().prefetch_related(
        'evaluaciones',
        'planes_mejoramiento'
    ).order_by('razon_social')
    
    for proveedor in proveedores:
        # Obtener la última evaluación
        evaluacion = proveedor.evaluaciones.order_by('-fecha').first()
        
        if evaluacion:
            # Obtener el plan asociado a esta evaluación
            plan = PlanMejoramiento.objects.filter(
                proveedor=proveedor,
                evaluacion=evaluacion
            ).order_by('-fecha_creacion').first()
            
            proveedores_lista.append({
                'proveedor': proveedor,
                'evaluacion': evaluacion,
                'plan': plan
            })
    
    # Calcular estadísticas (Parametrización ITCO-ISA)
    total_proveedores = len(proveedores_lista)
    proveedores_bajo_80 = sum(1 for p in proveedores_lista if p['evaluacion'].puntaje < 80)
    planes_pendientes = PlanMejoramiento.objects.filter(estado='ENVIADO').count()
    planes_aprobados = PlanMejoramiento.objects.filter(estado='APROBADO').count()
    
    context = {
        'proveedores': proveedores_lista,
        'total_proveedores': total_proveedores,
        'proveedores_bajo_80': proveedores_bajo_80,
        'planes_pendientes': planes_pendientes,
        'planes_aprobados': planes_aprobados,
    }

    return render(request, 'planes/lista_proveedores_simple.html', context)


@login_required
def dashboard_analytics(request):
    """Dashboard avanzado con analytics y visualizaciones"""
    # Verificar permisos (Gestores y Técnicos)
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos para acceder a este dashboard')
        return redirect('proveedor_dashboard')

    # ========== OBTENER FILTROS ==========
    filtro_proveedor = request.GET.get('proveedor', '')
    filtro_documento = request.GET.get('documento', '')

    # ========== APLICAR FILTROS A EVALUACIONES ==========
    evaluaciones_filtradas = Evaluacion.objects.all()

    if filtro_proveedor:
        evaluaciones_filtradas = evaluaciones_filtradas.filter(
            Q(proveedor__razon_social__icontains=filtro_proveedor) |
            Q(proveedor__nit__icontains=filtro_proveedor)
        )

    if filtro_documento:
        evaluaciones_filtradas = evaluaciones_filtradas.filter(
            Q(numero_contrato__icontains=filtro_documento) |
            Q(subcategoria__icontains=filtro_documento)
        )

    # ========== ESTADÍSTICAS GENERALES ==========
    total_proveedores = Proveedor.objects.filter(activo=True).count()
    total_evaluaciones = evaluaciones_filtradas.count()

    # Aplicar filtros a planes relacionados con las evaluaciones filtradas
    if filtro_proveedor or filtro_documento:
        evaluaciones_ids = evaluaciones_filtradas.values_list('id', flat=True)
        planes_filtrados = PlanMejoramiento.objects.filter(evaluacion_id__in=evaluaciones_ids)
    else:
        planes_filtrados = PlanMejoramiento.objects.all()

    total_planes = planes_filtrados.count()

    # Promedios y agregaciones (sobre evaluaciones filtradas)
    promedio_puntaje_global = evaluaciones_filtradas.aggregate(Avg('puntaje'))['puntaje__avg'] or 0
    promedio_gestion = evaluaciones_filtradas.aggregate(Avg('puntaje_gestion'))['puntaje_gestion__avg'] or 0
    promedio_calidad = evaluaciones_filtradas.aggregate(Avg('puntaje_calidad'))['puntaje_calidad__avg'] or 0
    promedio_oportunidad = evaluaciones_filtradas.aggregate(Avg('puntaje_oportunidad'))['puntaje_oportunidad__avg'] or 0
    promedio_ambiental = evaluaciones_filtradas.aggregate(Avg('puntaje_ambiental_social'))['puntaje_ambiental_social__avg'] or 0
    promedio_sst = evaluaciones_filtradas.aggregate(Avg('puntaje_sst'))['puntaje_sst__avg'] or 0

    # ========== DISTRIBUCIÓN DE EVALUACIONES ==========
    # Solo evaluaciones que requieren plan de mejoramiento (puntaje < 80)
    evaluaciones_satisfactorias = 0  # No se cargan al sistema
    evaluaciones_aceptables = evaluaciones_filtradas.filter(puntaje__gte=60, puntaje__lt=80).count()
    evaluaciones_criticas = evaluaciones_filtradas.filter(puntaje__lt=60).count()

    # ========== ESTADOS DE PLANES ==========
    planes_borrador = planes_filtrados.filter(estado='BORRADOR').count()
    planes_enviados = planes_filtrados.filter(estado='ENVIADO').count()
    planes_revision = planes_filtrados.filter(estado__in=['EN_REVISION', 'ESPERANDO_APROBACION']).count()
    planes_requiere_ajustes = planes_filtrados.filter(estado='REQUIERE_AJUSTES').count()
    planes_aprobados = planes_filtrados.filter(estado='APROBADO').count()
    planes_rechazados = planes_filtrados.filter(estado='RECHAZADO').count()

    # ========== TENDENCIAS TEMPORALES ==========
    # Evaluaciones por mes (últimos 6 meses)
    fecha_inicio = date.today() - timedelta(days=180)
    evaluaciones_recientes = evaluaciones_filtradas.filter(fecha__gte=fecha_inicio).order_by('fecha')

    # Agrupar por mes
    evaluaciones_por_mes = defaultdict(lambda: {'count': 0, 'promedio': 0, 'suma': 0})
    for eval in evaluaciones_recientes:
        mes_key = eval.fecha.strftime('%Y-%m')
        evaluaciones_por_mes[mes_key]['count'] += 1
        evaluaciones_por_mes[mes_key]['suma'] += eval.puntaje

    # Calcular promedios
    for mes in evaluaciones_por_mes:
        if evaluaciones_por_mes[mes]['count'] > 0:
            evaluaciones_por_mes[mes]['promedio'] = round(
                evaluaciones_por_mes[mes]['suma'] / evaluaciones_por_mes[mes]['count'], 1
            )

    # Convertir a listas para Chart.js
    meses_labels = sorted(evaluaciones_por_mes.keys())
    evaluaciones_counts = [evaluaciones_por_mes[m]['count'] for m in meses_labels]
    evaluaciones_promedios = [evaluaciones_por_mes[m]['promedio'] for m in meses_labels]

    # Formatear labels de meses
    meses_labels_formatted = []
    for m in meses_labels:
        try:
            fecha_mes = datetime.strptime(m, '%Y-%m')
            meses_labels_formatted.append(fecha_mes.strftime('%b %Y'))
        except:
            meses_labels_formatted.append(m)

    # ========== TOP 5 EVALUACIONES ACEPTABLES Y CRÍTICAS ==========
    # Total de evaluaciones aceptables y críticas
    total_evaluaciones_aceptables = evaluaciones_filtradas.filter(
        puntaje__gte=60,
        puntaje__lt=80
    ).count()

    total_evaluaciones_criticas = evaluaciones_filtradas.filter(
        puntaje__lt=60
    ).count()

    # Top 5 evaluaciones aceptables (60-79) ordenadas de menor a mayor
    top_5_aceptables = evaluaciones_filtradas.filter(
        puntaje__gte=60,
        puntaje__lt=80
    ).select_related('proveedor').order_by('puntaje')[:5]

    # Top 5 evaluaciones críticas (<60) ordenadas de menor a mayor (empezando desde 0)
    top_5_criticas = evaluaciones_filtradas.filter(
        puntaje__lt=60
    ).select_related('proveedor').order_by('puntaje')[:5]

    # ========== DISTRIBUCIÓN POR CRITERIOS ==========
    # Para el gráfico de radar de promedios por criterio
    criterios_labels = ['Gestión', 'Calidad', 'Oportunidad', 'Ambiental/Social', 'SST']
    criterios_valores = [
        round(promedio_gestion, 1),
        round(promedio_calidad, 1),
        round(promedio_oportunidad, 1),
        round(promedio_ambiental, 1),
        round(promedio_sst, 1)
    ]

    # ========== TIEMPO DE RESPUESTA DE PLANES ==========
    planes_con_tiempo = planes_filtrados.filter(
        fecha_envio__isnull=False,
        fecha_aprobacion__isnull=False
    )

    tiempos_respuesta = []
    for plan in planes_con_tiempo:
        dias = (plan.fecha_aprobacion.date() - plan.fecha_envio.date()).days
        tiempos_respuesta.append(dias)

    tiempo_promedio_respuesta = sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0

    # ========== PLANES VENCIDOS Y PRÓXIMOS A VENCER ==========
    planes_activos = planes_filtrados.filter(
        estado__in=['ENVIADO', 'EN_REVISION', 'ESPERANDO_APROBACION', 'REQUIERE_AJUSTES']
    )

    planes_vencidos = []
    planes_por_vencer = []

    for plan in planes_activos:
        if plan.fecha_limite:
            dias_restantes = (plan.fecha_limite - date.today()).days
            if dias_restantes < 0:
                planes_vencidos.append(plan)
            elif dias_restantes <= 5:
                planes_por_vencer.append(plan)

    # ========== ACTIVIDAD RECIENTE ==========
    actividad_reciente = HistorialEstado.objects.select_related(
        'plan__proveedor', 'usuario'
    ).order_by('-fecha_cambio')[:10]

    # ========== PREPARAR DATOS PARA JSON (CHARTS) ==========
    context = {
        # Filtros
        'filtro_proveedor': filtro_proveedor,
        'filtro_documento': filtro_documento,

        # Estadísticas generales
        'total_proveedores': total_proveedores,
        'total_evaluaciones': total_evaluaciones,
        'total_planes': total_planes,
        'promedio_puntaje_global': round(promedio_puntaje_global, 1),

        # Distribución de evaluaciones
        'evaluaciones_satisfactorias': evaluaciones_satisfactorias,
        'evaluaciones_aceptables': evaluaciones_aceptables,
        'evaluaciones_criticas': evaluaciones_criticas,

        # Estados de planes
        'planes_borrador': planes_borrador,
        'planes_enviados': planes_enviados,
        'planes_revision': planes_revision,
        'planes_requiere_ajustes': planes_requiere_ajustes,
        'planes_aprobados': planes_aprobados,
        'planes_rechazados': planes_rechazados,

        # Promedios por criterio
        'promedio_gestion': round(promedio_gestion, 1),
        'promedio_calidad': round(promedio_calidad, 1),
        'promedio_oportunidad': round(promedio_oportunidad, 1),
        'promedio_ambiental': round(promedio_ambiental, 1),
        'promedio_sst': round(promedio_sst, 1),

        # Top 5 evaluaciones
        'top_5_aceptables': top_5_aceptables,
        'top_5_criticas': top_5_criticas,
        'total_evaluaciones_aceptables': total_evaluaciones_aceptables,
        'total_evaluaciones_criticas': total_evaluaciones_criticas,

        # Tiempo de respuesta
        'tiempo_promedio_respuesta': round(tiempo_promedio_respuesta, 1),

        # Alertas
        'planes_vencidos': planes_vencidos,
        'planes_por_vencer': planes_por_vencer,

        # Actividad reciente
        'actividad_reciente': actividad_reciente,

        # Datos para gráficos (JSON)
        'chart_data': json.dumps({
            'meses_labels': meses_labels_formatted,
            'evaluaciones_counts': evaluaciones_counts,
            'evaluaciones_promedios': evaluaciones_promedios,
            'criterios_labels': criterios_labels,
            'criterios_valores': criterios_valores,
            'distribucion_evaluaciones': [
                evaluaciones_satisfactorias,
                evaluaciones_aceptables,
                evaluaciones_criticas
            ],
            'distribucion_planes': [
                planes_borrador,
                planes_enviados,
                planes_revision,
                planes_requiere_ajustes,
                planes_aprobados,
                planes_rechazados
            ]
        })
    }

    return render(request, 'planes/dashboard_analytics.html', context)


@login_required
def manual_usuario(request):
    """Vista para mostrar el manual de usuario"""
    return render(request, 'planes/manual_usuario.html')