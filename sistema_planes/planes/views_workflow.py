"""
Vistas para la gestión del workflow completo de planes de mejoramiento
Incluye: radicación, cambios de estado, aclaraciones, etc.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import PlanMejoramiento, HistorialEstado, Proveedor
from .workflows import PlanWorkflow


# ============= VISTAS DE CAMBIO DE ESTADO =============

@login_required
def cambiar_estado_plan(request, plan_id):
    """
    Vista genérica para cambiar el estado de un plan
    Valida permisos y transiciones permitidas usando PlanWorkflow
    """
    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    # Verificar permisos básicos
    es_proveedor = hasattr(request.user, 'proveedor')
    es_gestor = hasattr(request.user, 'perfil') and request.user.perfil.es_gestor
    es_tecnico = hasattr(request.user, 'perfil') and request.user.perfil.es_tecnico
    es_gestor_compras = hasattr(request.user, 'perfil') and request.user.perfil.es_gestor_compras

    # Si es proveedor, verificar que sea su plan
    if es_proveedor:
        proveedor = request.user.proveedor
        if plan.proveedor != proveedor:
            messages.error(request, 'No tiene permisos para modificar este plan')
            return redirect('proveedor_dashboard')

    if request.method == 'POST':
        nuevo_estado = request.POST.get('nuevo_estado')
        comentario = request.POST.get('comentario', '')

        # Preparar kwargs adicionales según el estado
        kwargs = {}

        if nuevo_estado == 'PM_RADICADO':
            kwargs['numero_radicado'] = request.POST.get('numero_radicado', '')

        if nuevo_estado == 'RECHAZADO':
            kwargs['motivo_rechazo'] = request.POST.get('motivo_rechazo', '')

        if nuevo_estado == 'ACLARACION':
            kwargs['observaciones_aclaracion'] = request.POST.get('observaciones_aclaracion', '')

        # Manejar archivo de carta de evaluación
        if 'carta_evaluacion' in request.FILES:
            kwargs['carta_evaluacion'] = request.FILES['carta_evaluacion']

        # Realizar la transición usando el workflow
        exito, mensaje = PlanWorkflow.transicionar(
            plan=plan,
            nuevo_estado=nuevo_estado,
            usuario=request.user,
            comentario=comentario,
            **kwargs
        )

        if exito:
            messages.success(request, mensaje)
        else:
            messages.error(request, mensaje)

        # Redirigir según el tipo de usuario
        if es_proveedor:
            return redirect('ver_plan', plan_id=plan.id)
        else:
            return redirect('ver_plan', plan_id=plan.id)

    # GET: Mostrar formulario con estados disponibles
    estados_disponibles = PlanWorkflow.obtener_proximos_estados(plan, request.user)

    context = {
        'plan': plan,
        'estados_disponibles': estados_disponibles,
        'es_proveedor': es_proveedor,
        'es_gestor': es_gestor,
        'es_tecnico': es_tecnico,
        'es_gestor_compras': es_gestor_compras,
    }

    return render(request, 'planes/cambiar_estado.html', context)


@login_required
def radicar_plan(request, plan_id):
    """
    Vista específica para radicar un plan (asignar número de radicado)
    Solo accesible por Gestor de Compras
    """
    # Verificar permisos
    if not (hasattr(request.user, 'perfil') and request.user.perfil.es_gestor_compras):
        messages.error(request, 'No tiene permisos para radicar planes')
        return redirect('tecnico_panel')

    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    # Verificar que el plan esté en estado correcto
    if plan.estado != 'EN_RADICACION':
        messages.warning(request, f'El plan debe estar en estado "En Radicación" para ser radicado. Estado actual: {plan.get_estado_display()}')
        return redirect('ver_plan', plan_id=plan.id)

    if request.method == 'POST':
        numero_radicado = request.POST.get('numero_radicado', '').strip()
        comentario = request.POST.get('comentario', '')

        if not numero_radicado:
            messages.error(request, 'Debe proporcionar un número de radicado')
            return render(request, 'planes/radicar_plan.html', {'plan': plan})

        # Realizar transición a PM_RADICADO
        exito, mensaje = PlanWorkflow.transicionar(
            plan=plan,
            nuevo_estado='PM_RADICADO',
            usuario=request.user,
            comentario=comentario or f'Plan radicado con número: {numero_radicado}',
            numero_radicado=numero_radicado
        )

        if exito:
            messages.success(request, f'Plan radicado exitosamente. Número de radicado: {numero_radicado}')
            return redirect('ver_plan', plan_id=plan.id)
        else:
            messages.error(request, mensaje)

    context = {
        'plan': plan,
    }

    return render(request, 'planes/radicar_plan.html', context)


@login_required
def rechazar_plan(request, plan_id):
    """
    Vista para rechazar un plan durante el proceso de radicación
    """
    # Verificar permisos
    if not (hasattr(request.user, 'perfil') and
            (request.user.perfil.es_gestor_compras or request.user.perfil.es_gestor)):
        messages.error(request, 'No tiene permisos para rechazar planes')
        return redirect('tecnico_panel')

    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    if request.method == 'POST':
        motivo_rechazo = request.POST.get('motivo_rechazo', '').strip()

        if not motivo_rechazo:
            messages.error(request, 'Debe proporcionar un motivo de rechazo')
            return render(request, 'planes/rechazar_plan.html', {'plan': plan})

        # Realizar transición a RECHAZADO
        exito, mensaje = PlanWorkflow.transicionar(
            plan=plan,
            nuevo_estado='RECHAZADO',
            usuario=request.user,
            comentario=f'Plan rechazado: {motivo_rechazo}',
            motivo_rechazo=motivo_rechazo
        )

        if exito:
            messages.success(request, 'Plan rechazado exitosamente')
            return redirect('ver_plan', plan_id=plan.id)
        else:
            messages.error(request, mensaje)

    context = {
        'plan': plan,
    }

    return render(request, 'planes/rechazar_plan.html', context)


@login_required
def solicitar_aclaracion(request, plan_id):
    """
    Vista para solicitar aclaración cuando un plan no ha sido recibido
    """
    # Verificar permisos (técnico o gestor)
    if not (hasattr(request.user, 'perfil') and
            (request.user.perfil.es_tecnico or request.user.perfil.es_gestor)):
        messages.error(request, 'No tiene permisos para solicitar aclaraciones')
        return redirect('login')

    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    # Verificar que el plan esté en estado NO_RECIBIDO
    if plan.estado != 'NO_RECIBIDO':
        messages.warning(request, 'Solo se pueden solicitar aclaraciones para planes no recibidos')
        return redirect('ver_plan', plan_id=plan.id)

    if request.method == 'POST':
        observaciones = request.POST.get('observaciones_aclaracion', '')

        # Realizar transición a ACLARACION
        exito, mensaje = PlanWorkflow.transicionar(
            plan=plan,
            nuevo_estado='ACLARACION',
            usuario=request.user,
            comentario=f'Solicitud de aclaración: {observaciones}',
            observaciones_aclaracion=observaciones
        )

        if exito:
            messages.success(request, 'Solicitud de aclaración enviada al proveedor')
            return redirect('ver_plan', plan_id=plan.id)
        else:
            messages.error(request, mensaje)

    context = {
        'plan': plan,
    }

    return render(request, 'planes/solicitar_aclaracion.html', context)


@login_required
def enviar_carta_evaluacion(request, plan_id):
    """
    Vista para que CS envíe la carta de evaluación al proveedor
    Inicia el proceso de firmas
    """
    # Verificar permisos (gestor o técnico)
    if not (hasattr(request.user, 'perfil') and
            (request.user.perfil.es_gestor or request.user.perfil.es_tecnico)):
        messages.error(request, 'No tiene permisos para enviar cartas de evaluación')
        return redirect('login')

    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    if request.method == 'POST':
        carta_archivo = request.FILES.get('carta_evaluacion')
        comentario = request.POST.get('comentario', '')

        if not carta_archivo:
            messages.error(request, 'Debe adjuntar la carta de evaluación')
            return render(request, 'planes/enviar_carta.html', {'plan': plan})

        # Realizar transición a PROCESO_FIRMAS
        exito, mensaje = PlanWorkflow.transicionar(
            plan=plan,
            nuevo_estado='PROCESO_FIRMAS',
            usuario=request.user,
            comentario=comentario or 'Carta de evaluación enviada para proceso de firmas',
            carta_evaluacion=carta_archivo
        )

        if exito:
            messages.success(request, 'Carta de evaluación enviada. El proveedor debe firmar y enviar el plan.')
            return redirect('ver_plan', plan_id=plan.id)
        else:
            messages.error(request, mensaje)

    context = {
        'plan': plan,
    }

    return render(request, 'planes/enviar_carta.html', context)


@login_required
def marcar_falta_etica(request, plan_id):
    """
    Vista para marcar a un proveedor con falta de ética (suspensión 5 años)
    """
    # Solo gestores pueden hacer esto
    if not (hasattr(request.user, 'perfil') and request.user.perfil.es_gestor):
        messages.error(request, 'No tiene permisos para esta acción')
        return redirect('login')

    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        confirmacion = request.POST.get('confirmacion', '')

        if confirmacion != 'SUSPENDER':
            messages.error(request, 'Debe escribir "SUSPENDER" para confirmar esta acción')
            return render(request, 'planes/marcar_falta_etica.html', {'plan': plan})

        # Realizar transición a FALTA_ETICA
        exito, mensaje = PlanWorkflow.transicionar(
            plan=plan,
            nuevo_estado='FALTA_ETICA',
            usuario=request.user,
            comentario=f'Proveedor suspendido por 5 años. Motivo: {motivo}'
        )

        if exito:
            messages.warning(request, f'Proveedor {plan.proveedor.razon_social} suspendido por falta de ética')
            return redirect('lista_proveedores')
        else:
            messages.error(request, mensaje)

    context = {
        'plan': plan,
    }

    return render(request, 'planes/marcar_falta_etica.html', context)


# ============= VISTAS DE CONSULTA =============

@login_required
def historial_plan(request, plan_id):
    """
    Vista para ver el historial completo de un plan
    """
    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    # Verificar permisos
    es_proveedor = hasattr(request.user, 'proveedor')
    if es_proveedor and plan.proveedor != request.user.proveedor:
        messages.error(request, 'No tiene permisos para ver este plan')
        return redirect('proveedor_dashboard')

    historial = plan.historial.all().order_by('-fecha_cambio')

    context = {
        'plan': plan,
        'historial': historial,
        'tipo_flujo': PlanWorkflow.obtener_tipo_flujo(plan.estado),
        'es_estado_final': PlanWorkflow.es_estado_final(plan.estado),
        'es_estado_activo': PlanWorkflow.es_estado_activo(plan.estado),
    }

    return render(request, 'planes/historial_plan.html', context)


@login_required
def planes_pendientes_radicacion(request):
    """
    Vista para gestores de compras: lista de planes pendientes de radicar
    """
    if not (hasattr(request.user, 'perfil') and request.user.perfil.es_gestor_compras):
        messages.error(request, 'No tiene permisos para acceder a esta sección')
        return redirect('login')

    # Obtener planes en estado EN_RADICACION
    planes = PlanMejoramiento.objects.filter(
        estado='EN_RADICACION'
    ).select_related('proveedor', 'evaluacion').order_by('-fecha_revision')

    context = {
        'planes': planes,
        'total_pendientes': planes.count(),
    }

    return render(request, 'planes/planes_pendientes_radicacion.html', context)


@login_required
def planes_no_recibidos(request):
    """
    Vista para ver planes que no han sido recibidos (pasaron 30 días)
    """
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos para acceder a esta sección')
        return redirect('proveedor_dashboard')

    # Obtener planes en estado NO_RECIBIDO
    planes = PlanMejoramiento.objects.filter(
        estado='NO_RECIBIDO'
    ).select_related('proveedor', 'evaluacion').order_by('-dias_sin_respuesta')

    context = {
        'planes': planes,
        'total_no_recibidos': planes.count(),
    }

    return render(request, 'planes/planes_no_recibidos.html', context)


# ============= API/AJAX =============

@login_required
def obtener_proximos_estados_ajax(request, plan_id):
    """
    API para obtener los próximos estados disponibles de un plan
    Retorna JSON con los estados a los que se puede transicionar
    """
    plan = get_object_or_404(PlanMejoramiento, id=plan_id)

    # Obtener estados disponibles para el usuario actual
    estados_disponibles = PlanWorkflow.obtener_proximos_estados(plan, request.user)

    return JsonResponse({
        'estado_actual': plan.estado,
        'estado_actual_display': plan.get_estado_display(),
        'estados_disponibles': [
            {'codigo': codigo, 'nombre': nombre}
            for codigo, nombre in estados_disponibles
        ],
        'tipo_flujo': PlanWorkflow.obtener_tipo_flujo(plan.estado),
        'es_estado_final': PlanWorkflow.es_estado_final(plan.estado),
    })
