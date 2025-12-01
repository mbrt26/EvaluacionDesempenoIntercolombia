"""
Vistas específicas para cada perfil de usuario
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import PerfilUsuario, Proveedor, Evaluacion, PlanMejoramiento, HistorialEstado
from .forms import PlanMejoramientoForm
import logging

logger = logging.getLogger(__name__)


def get_user_profile(user):
    """Obtener o crear el perfil del usuario"""
    try:
        return user.perfil
    except PerfilUsuario.DoesNotExist:
        # Si el usuario tiene un proveedor asociado, es proveedor
        if hasattr(user, 'proveedor'):
            return PerfilUsuario.objects.create(user=user, tipo_perfil='PROVEEDOR')
        # Por defecto, crear como técnico
        return PerfilUsuario.objects.create(user=user, tipo_perfil='TECNICO')


@login_required
def dashboard_redirect(request):
    """Redirigir al dashboard correspondiente según el perfil"""
    perfil = get_user_profile(request.user)

    # Si requiere cambio de contraseña, redirigir
    if perfil.requiere_cambio_password:
        messages.warning(request, 'Por seguridad, debe cambiar su contraseña en el primer acceso.')
        return redirect('cambiar_password')

    if perfil.es_gestor:
        return redirect('gestor_dashboard')
    elif perfil.es_gestor_compras:
        return redirect('gestor_compras_dashboard')
    elif perfil.es_tecnico:
        return redirect('tecnico_dashboard')
    elif perfil.es_proveedor:
        return redirect('proveedor_dashboard')
    else:
        messages.error(request, 'Perfil de usuario no reconocido')
        return redirect('login')


@login_required
def dashboard_gestor(request):
    """Dashboard para el Gestor de Planes de Mejoramiento"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para acceder a esta sección')
        return redirect('dashboard_redirect')

    # Estadísticas generales
    total_proveedores = Proveedor.objects.count()
    total_evaluaciones = Evaluacion.objects.count()
    total_planes = PlanMejoramiento.objects.count()

    # Planes por estado
    planes_borrador = PlanMejoramiento.objects.filter(estado='BORRADOR').count()
    planes_enviados = PlanMejoramiento.objects.filter(estado='ENVIADO').count()
    planes_revision = PlanMejoramiento.objects.filter(estado='EN_REVISION').count()
    planes_aprobados = PlanMejoramiento.objects.filter(estado='APROBADO').count()

    # Evaluaciones recientes
    evaluaciones_recientes = Evaluacion.objects.select_related('proveedor').order_by('fecha')[:5]

    # Planes pendientes de revisión
    planes_pendientes = PlanMejoramiento.objects.filter(
        estado__in=['ENVIADO', 'EN_REVISION', 'ESPERANDO_APROBACION']
    ).select_related('proveedor', 'evaluacion').order_by('fecha_envio')[:10]

    context = {
        'perfil': perfil,
        'estadisticas': {
            'total_proveedores': total_proveedores,
            'total_evaluaciones': total_evaluaciones,
            'total_planes': total_planes,
            'planes_borrador': planes_borrador,
            'planes_enviados': planes_enviados,
            'planes_revision': planes_revision,
            'planes_aprobados': planes_aprobados,
        },
        'evaluaciones_recientes': evaluaciones_recientes,
        'planes_pendientes': planes_pendientes,
    }

    return render(request, 'planes/dashboard_gestor.html', context)


@login_required
def dashboard_gestor_compras(request):
    """Dashboard de solo lectura para el Gestor de Compras"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor_compras:
        messages.error(request, 'No tiene permisos para acceder a esta sección')
        return redirect('dashboard_redirect')

    # Estadísticas generales
    total_proveedores = Proveedor.objects.count()
    total_evaluaciones = Evaluacion.objects.count()
    total_planes = PlanMejoramiento.objects.count()

    # Estadísticas de evaluaciones
    evaluaciones_satisfactorias = Evaluacion.objects.filter(puntaje__gte=80).count()
    evaluaciones_aceptables = Evaluacion.objects.filter(puntaje__gte=60, puntaje__lt=80).count()
    evaluaciones_criticas = Evaluacion.objects.filter(puntaje__lt=60).count()

    # Planes por estado
    planes_borrador = PlanMejoramiento.objects.filter(estado='BORRADOR').count()
    planes_enviados = PlanMejoramiento.objects.filter(estado='ENVIADO').count()
    planes_revision = PlanMejoramiento.objects.filter(estado='EN_REVISION').count()
    planes_requiere_ajustes = PlanMejoramiento.objects.filter(estado='REQUIERE_AJUSTES').count()
    planes_aprobados = PlanMejoramiento.objects.filter(estado='APROBADO').count()
    planes_rechazados = PlanMejoramiento.objects.filter(estado='RECHAZADO').count()

    # Calcular promedio de puntajes
    from django.db.models import Avg
    promedio_puntaje = Evaluacion.objects.aggregate(Avg('puntaje'))['puntaje__avg'] or 0
    promedio_puntaje = round(promedio_puntaje, 1)

    # Evaluaciones recientes (últimas 10)
    evaluaciones_recientes = Evaluacion.objects.select_related('proveedor', 'tecnico_asignado').order_by('-fecha')[:10]

    # Planes recientes
    planes_recientes = PlanMejoramiento.objects.select_related('proveedor', 'evaluacion').order_by('-fecha_creacion')[:10]

    context = {
        'perfil': perfil,
        'estadisticas': {
            'total_proveedores': total_proveedores,
            'total_evaluaciones': total_evaluaciones,
            'total_planes': total_planes,
            'promedio_puntaje': promedio_puntaje,
            'evaluaciones_satisfactorias': evaluaciones_satisfactorias,
            'evaluaciones_aceptables': evaluaciones_aceptables,
            'evaluaciones_criticas': evaluaciones_criticas,
            'planes_borrador': planes_borrador,
            'planes_enviados': planes_enviados,
            'planes_revision': planes_revision,
            'planes_requiere_ajustes': planes_requiere_ajustes,
            'planes_aprobados': planes_aprobados,
            'planes_rechazados': planes_rechazados,
        },
        'evaluaciones_recientes': evaluaciones_recientes,
        'planes_recientes': planes_recientes,
    }

    return render(request, 'planes/dashboard_gestor_compras.html', context)


@login_required
def dashboard_tecnico(request):
    """Dashboard para el Técnico"""
    perfil = get_user_profile(request.user)
    
    if not perfil.es_tecnico:
        messages.error(request, 'No tiene permisos para acceder a esta sección')
        return redirect('dashboard_redirect')
    
    # Planes asignados para revisión
    planes_para_revisar = PlanMejoramiento.objects.filter(
        evaluacion__tecnico_asignado=request.user,
        estado__in=['ENVIADO', 'EN_REVISION', 'ESPERANDO_APROBACION']
    ).select_related('proveedor', 'evaluacion').order_by('fecha_envio')
    
    # Estadísticas del técnico
    total_asignados = planes_para_revisar.count()
    aprobados_mes = PlanMejoramiento.objects.filter(
        evaluacion__tecnico_asignado=request.user,
        estado='APROBADO',
        fecha_aprobacion__month=timezone.now().month
    ).count()
    
    # Redirigir al panel técnico que ya existe y funciona
    return redirect('tecnico_panel')


@login_required
def revisar_plan(request, plan_id):
    """Vista para que el técnico o gestor revise y apruebe/rechace planes"""
    perfil = get_user_profile(request.user)

    # Permitir acceso a técnicos y gestores
    if not (perfil.es_tecnico or perfil.es_gestor):
        messages.error(request, 'No tiene permisos para revisar planes')
        return redirect('dashboard_redirect')

    plan = get_object_or_404(PlanMejoramiento, id=plan_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        comentarios = request.POST.get('comentarios', '')
        
        estado_anterior = plan.estado
        
        if accion == 'aprobar':
            plan.estado = 'APROBADO'
            plan.fecha_aprobacion = timezone.now()
            plan.comentarios_tecnico = comentarios
            plan.revisado_por = request.user
            plan.fecha_revision = timezone.now()
            messages.success(request, 'Plan aprobado exitosamente')
            
        elif accion == 'solicitar_ajustes':
            plan.estado = 'SOLICITUD_AJUSTES'
            plan.comentarios_tecnico = comentarios
            plan.revisado_por = request.user
            plan.fecha_revision = timezone.now()
            messages.info(request, 'Se ha solicitado ajustes al proveedor')
            
        elif accion == 'rechazar':
            plan.estado = 'RECHAZADO'
            plan.comentarios_tecnico = comentarios
            plan.revisado_por = request.user
            plan.fecha_revision = timezone.now()
            messages.warning(request, 'Plan rechazado')
        
        plan.save()
        
        # Registrar en historial
        HistorialEstado.objects.create(
            plan=plan,
            estado_anterior=estado_anterior,
            estado_nuevo=plan.estado,
            usuario=request.user,
            comentario=comentarios
        )

        return redirect('tecnico_dashboard')
    
    context = {
        'plan': plan,
        'perfil': perfil,
    }
    
    return render(request, 'planes/revisar_plan.html', context)


@login_required
def cambiar_password(request):
    """Vista para cambiar la contraseña"""
    perfil = get_user_profile(request.user)
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            # Validar contraseña segura
            new_password = form.cleaned_data['new_password1']
            if not validar_password_segura(new_password):
                messages.error(
                    request, 
                    'La contraseña debe tener al menos 8 caracteres, incluyendo mayúsculas, minúsculas, números y caracteres especiales.'
                )
                return render(request, 'planes/cambiar_password.html', {'form': form})
            
            user = form.save()
            update_session_auth_hash(request, user)
            
            # Marcar que ya no requiere cambio de contraseña
            perfil.requiere_cambio_password = False
            perfil.save()
            
            messages.success(request, 'Contraseña actualizada exitosamente')
            return redirect('dashboard_redirect')
        else:
            messages.error(request, 'Por favor corrija los errores del formulario')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'planes/cambiar_password.html', {
        'form': form,
        'perfil': perfil,
    })


def validar_password_segura(password):
    """Validar que la contraseña sea segura"""
    import re
    
    # Al menos 8 caracteres
    if len(password) < 8:
        return False
    
    # Al menos una mayúscula
    if not re.search(r'[A-Z]', password):
        return False
    
    # Al menos una minúscula
    if not re.search(r'[a-z]', password):
        return False
    
    # Al menos un número
    if not re.search(r'[0-9]', password):
        return False
    
    # Al menos un carácter especial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True


@login_required
def cargar_evaluacion_automatica(request):
    """Vista para cargar evaluaciones automáticamente desde lista PM"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para cargar evaluaciones')
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        # Aquí se implementaría la lógica para cargar desde SharePoint/PowerApp
        # Por ahora, simulamos la carga

        try:
            with transaction.atomic():
                # Obtener proveedor y técnico
                proveedor_id = request.POST.get('proveedor_id')
                tecnico_id = request.POST.get('tecnico_id')

                if not proveedor_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Debe seleccionar un proveedor'
                    })

                if not tecnico_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Debe seleccionar un técnico responsable'
                    })

                proveedor = get_object_or_404(Proveedor, id=proveedor_id)
                tecnico = get_object_or_404(User, id=tecnico_id)

                # Obtener puntaje total desde el formulario dinámico
                puntaje_total = int(request.POST.get('puntaje_total', 0))

                # Valores por defecto para compatibilidad con modelo existente
                puntaje_gestion = 0
                puntaje_calidad = 0
                puntaje_oportunidad = 0
                puntaje_ambiental_social = 0
                puntaje_sst = 0

                # Crear evaluación
                evaluacion = Evaluacion.objects.create(
                    proveedor=proveedor,
                    tecnico_asignado=tecnico,
                    numero_contrato=request.POST.get('numero_contrato'),
                    tipo_contrato=request.POST.get('tipo_contrato'),
                    subcategoria=request.POST.get('subcategoria'),
                    puntaje=puntaje_total,
                    puntaje_gestion=puntaje_gestion,
                    puntaje_calidad=puntaje_calidad,
                    puntaje_oportunidad=puntaje_oportunidad,
                    puntaje_ambiental_social=puntaje_ambiental_social,
                    puntaje_sst=puntaje_sst,
                    requiere_aprobacion_sst=request.POST.get('requiere_aprobacion_sst') == 'true',
                    requiere_aprobacion_ambiental=request.POST.get('requiere_aprobacion_ambiental') == 'true',
                    fecha_limite_aclaracion=request.POST.get('fecha_limite_aclaracion') or None,
                    fecha_limite_plan=request.POST.get('fecha_limite_plan') or None,
                    observaciones_gestion='',
                    observaciones_calidad='',
                    observaciones_oportunidad='',
                    observaciones_ambiental_social='',
                    observaciones_sst='',
                    observaciones_generales=request.POST.get('observaciones_generales', ''),
                    fecha=timezone.now().date(),
                )

                # Guardar tipo de calificación seleccionado en observaciones para referencia
                tipo_calificacion_id = request.POST.get('tipo_calificacion')
                if tipo_calificacion_id:
                    from .models import TipoCalificacion, CriterioEvaluacion, RespuestaEvaluacion
                    tipo = TipoCalificacion.objects.filter(id=tipo_calificacion_id).first()
                    if tipo:
                        obs_tipo = f"Tipo de Calificación: {tipo.nombre}"
                        if evaluacion.observaciones_generales:
                            evaluacion.observaciones_generales = obs_tipo + "\n\n" + evaluacion.observaciones_generales
                        else:
                            evaluacion.observaciones_generales = obs_tipo
                        evaluacion.save()

                        # Guardar las respuestas seleccionadas para cada criterio
                        for key, value in request.POST.items():
                            # Buscar campos de tipo criterio_X_opcion (la opción seleccionada)
                            if key.startswith('criterio_') and key.endswith('_opcion'):
                                # Extraer el id_criterio del nombre del campo
                                parts = key.split('_')
                                id_criterio = int(parts[1])  # criterio_X_opcion -> X
                                puntuacion = float(value)

                                # Buscar el criterio seleccionado en la BD
                                criterio_seleccionado = CriterioEvaluacion.objects.filter(
                                    tipo_calificacion=tipo,
                                    id_criterio=id_criterio,
                                    puntuacion_maxima=puntuacion
                                ).first()

                                if criterio_seleccionado:
                                    # Obtener observaciones del criterio si existen
                                    obs_key = f'criterio_{id_criterio}_obs'
                                    observaciones = request.POST.get(obs_key, '')

                                    # Crear registro de respuesta
                                    RespuestaEvaluacion.objects.create(
                                        evaluacion=evaluacion,
                                        criterio=criterio_seleccionado,
                                        id_criterio=id_criterio,
                                        puntuacion_obtenida=puntuacion,
                                        observaciones=observaciones
                                    )

                # Obtener estado del formulario
                estado_plan = request.POST.get('estado', 'BORRADOR')

                # Si requiere plan de mejoramiento, crearlo automáticamente
                if puntaje_total < 80:
                    # Calcular fecha de implementación (30 días desde hoy si no hay fecha límite)
                    from datetime import timedelta
                    fecha_implementacion = evaluacion.fecha_limite_plan or (timezone.now().date() + timedelta(days=30))

                    PlanMejoramiento.objects.create(
                        evaluacion=evaluacion,
                        proveedor=proveedor,
                        estado=estado_plan,
                        fecha_limite=evaluacion.fecha_limite_plan,
                        fecha_implementacion=fecha_implementacion,
                        analisis_causa='',
                        acciones_propuestas='',
                        responsable='',
                        indicadores_seguimiento=''
                    )

                    # Si es menor a 60, agregar nota especial
                    if puntaje_total < 60:
                        obs_especial = "Este contrato tiene calificación inferior a 60 y el plan de mejoramiento requiere aval de un tercero."
                        if evaluacion.observaciones_generales:
                            evaluacion.observaciones_generales += "\n\n" + obs_especial
                        else:
                            evaluacion.observaciones_generales = obs_especial
                        evaluacion.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Evaluación cargada exitosamente',
                    'evaluacion_id': evaluacion.id
                })

        except Exception as e:
            logger.error(f"Error al cargar evaluación: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    # Obtener lista de proveedores activos
    proveedores = Proveedor.objects.filter(activo=True).order_by('razon_social')

    # Obtener lista de técnicos activos
    tecnicos = User.objects.filter(
        perfil__tipo_perfil='TECNICO',
        is_active=True
    ).order_by('first_name', 'last_name')

    return render(request, 'planes/cargar_evaluacion.html', {
        'perfil': perfil,
        'proveedores': proveedores,
        'tecnicos': tecnicos
    })


@login_required
def lista_registros_gestor(request):
    """Vista de registros de proveedores y planes para el Gestor y Técnico - Muestra TODAS las evaluaciones"""
    perfil = get_user_profile(request.user)

    # Permitir acceso a gestores y técnicos
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos para ver esta página')
        return redirect('dashboard_redirect')

    # Obtener filtros
    filtro_busqueda = request.GET.get('busqueda', '').strip()
    filtro_estado = request.GET.get('estado', '')
    filtro_puntaje = request.GET.get('puntaje', '')
    filtro_requiere_plan = request.GET.get('requiere_plan', '')

    # Obtener todos los datos necesarios
    datos_proveedores = []

    # CAMBIO: Iterar sobre TODAS las evaluaciones en lugar de proveedores
    evaluaciones = Evaluacion.objects.select_related('proveedor').all().order_by('-fecha')

    # Aplicar filtro de búsqueda
    if filtro_busqueda:
        evaluaciones = evaluaciones.filter(
            Q(proveedor__razon_social__icontains=filtro_busqueda) |
            Q(proveedor__nit__icontains=filtro_busqueda) |
            Q(periodo__icontains=filtro_busqueda) |
            Q(numero_contrato__icontains=filtro_busqueda)
        )

    for evaluacion in evaluaciones:
        proveedor = evaluacion.proveedor

        # Obtener el plan si existe
        plan = PlanMejoramiento.objects.filter(
            proveedor=proveedor,
            evaluacion=evaluacion
        ).order_by('-fecha_creacion').first()

        # Determinar el estado del plan (Parametrización ITCO-ISA)
        estado_plan = "NO_APLICA"
        color_estado = "gris"
        requiere_plan = False

        if evaluacion.puntaje < 80:
            requiere_plan = True
            if plan:
                estado_plan = plan.get_estado_display()
                if plan.estado == 'APROBADO':
                    color_estado = "verde"
                elif plan.estado == 'RECHAZADO':
                    color_estado = "rojo"
                elif plan.estado == 'ENVIADO':
                    color_estado = "azul"
                elif plan.estado == 'REQUIERE_AJUSTES':
                    color_estado = "naranja"
                else:
                    color_estado = "amarillo"
            else:
                estado_plan = "SIN PLAN (Requerido)"
                color_estado = "rojo"
        else:
            estado_plan = "No requiere"
            color_estado = "verde-claro"

        # Aplicar filtros adicionales antes de agregar
        agregar = True

        # Filtro por estado del plan
        if filtro_estado:
            if plan:
                if filtro_estado != plan.estado:
                    agregar = False
            else:
                if filtro_estado == 'SIN_PLAN' and not (evaluacion.puntaje < 80):
                    agregar = False
                elif filtro_estado != 'SIN_PLAN':
                    agregar = False

        # Filtro por puntaje
        if filtro_puntaje and agregar:
            if filtro_puntaje == 'bajo_60' and evaluacion.puntaje >= 60:
                agregar = False
            elif filtro_puntaje == '60_80' and (evaluacion.puntaje < 60 or evaluacion.puntaje >= 80):
                agregar = False
            elif filtro_puntaje == 'sobre_80' and evaluacion.puntaje < 80:
                agregar = False

        # Filtro por si requiere plan
        if filtro_requiere_plan and agregar:
            if filtro_requiere_plan == 'si' and not requiere_plan:
                agregar = False
            elif filtro_requiere_plan == 'no' and requiere_plan:
                agregar = False

        if agregar:
            datos_proveedores.append({
                'proveedor': proveedor,
                'evaluacion': evaluacion,
                'plan': plan,
                'estado_plan': estado_plan,
                'color_estado': color_estado,
                'requiere_plan': requiere_plan,
            })

    # Calcular estadísticas
    total = len(datos_proveedores)
    requieren_plan = sum(1 for d in datos_proveedores if d['requiere_plan'])
    con_plan_aprobado = sum(1 for d in datos_proveedores if d['plan'] and d['plan'].estado == 'APROBADO')
    con_plan_pendiente = sum(1 for d in datos_proveedores if d['plan'] and d['plan'].estado in ['ENVIADO', 'EN_REVISION', 'ESPERANDO_APROBACION'])

    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(datos_proveedores, 20)  # 20 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'perfil': perfil,
        'datos': page_obj,
        'page_obj': page_obj,
        'estadisticas': {
            'total': total,
            'requieren_plan': requieren_plan,
            'aprobados': con_plan_aprobado,
            'pendientes': con_plan_pendiente,
        },
        'filtros': {
            'busqueda': filtro_busqueda,
            'estado': filtro_estado,
            'puntaje': filtro_puntaje,
            'requiere_plan': filtro_requiere_plan,
        }
    }

    return render(request, 'planes/registros_gestor.html', context)


# ==================== GESTIÓN DE USUARIOS ====================

@login_required
def lista_usuarios(request):
    """Vista para listar todos los usuarios del sistema"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para gestionar usuarios')
        return redirect('dashboard_redirect')

    # Obtener todos los usuarios con sus perfiles
    usuarios = User.objects.all().select_related('perfil').order_by('-date_joined')

    # Preparar datos de usuarios
    usuarios_data = []
    for usuario in usuarios:
        perfil_usuario = get_user_profile(usuario)

        # Verificar si tiene proveedor asociado
        proveedor = None
        if hasattr(usuario, 'proveedor'):
            proveedor = usuario.proveedor

        usuarios_data.append({
            'usuario': usuario,
            'perfil': perfil_usuario,
            'proveedor': proveedor,
            'tipo_display': perfil_usuario.get_tipo_perfil_display() if perfil_usuario else 'Sin perfil',
            'activo': perfil_usuario.activo if perfil_usuario else False,
        })

    # Obtener proveedores SIN usuario (pendientes de activación)
    proveedores_pendientes = Proveedor.objects.filter(user__isnull=True).order_by('fecha_registro')

    # Estadísticas
    total_usuarios = usuarios.count()
    total_gestores = PerfilUsuario.objects.filter(tipo_perfil='GESTOR').count()
    total_gestores_compras = PerfilUsuario.objects.filter(tipo_perfil='GESTOR_COMPRAS').count()
    total_tecnicos = PerfilUsuario.objects.filter(tipo_perfil='TECNICO').count()
    total_proveedores = Proveedor.objects.count()
    proveedores_sin_usuario = proveedores_pendientes.count()

    context = {
        'perfil': perfil,
        'usuarios': usuarios_data,
        'proveedores_pendientes': proveedores_pendientes,
        'estadisticas': {
            'total': total_usuarios,
            'gestores': total_gestores,
            'gestores_compras': total_gestores_compras,
            'tecnicos': total_tecnicos,
            'proveedores': total_proveedores,
            'pendientes': proveedores_sin_usuario,
        }
    }

    return render(request, 'planes/usuarios/lista_usuarios.html', context)


@login_required
def crear_usuario(request):
    """Vista para crear un nuevo usuario"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para crear usuarios')
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        tipo_perfil = request.POST.get('tipo_perfil')

        # Validar que no exista el username
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Ya existe un usuario con el username {username}')
            return render(request, 'planes/usuarios/crear_usuario.html', {'perfil': perfil})

        # Validar que no exista el email
        if email and User.objects.filter(email=email).exists():
            messages.error(request, f'Ya existe un usuario con el email {email}')
            return render(request, 'planes/usuarios/crear_usuario.html', {'perfil': perfil})

        try:
            with transaction.atomic():
                # Crear usuario
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                # Crear perfil
                PerfilUsuario.objects.create(
                    user=user,
                    tipo_perfil=tipo_perfil,
                    requiere_cambio_password=True,
                    activo=True
                )

                messages.success(request, f'Usuario {username} creado exitosamente')
                return redirect('gestor_lista_usuarios')

        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
            return render(request, 'planes/usuarios/crear_usuario.html', {'perfil': perfil})

    context = {
        'perfil': perfil,
    }
    return render(request, 'planes/usuarios/crear_usuario.html', context)


@login_required
def editar_usuario(request, user_id):
    """Vista para editar un usuario existente"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para editar usuarios')
        return redirect('dashboard_redirect')

    usuario = get_object_or_404(User, id=user_id)
    perfil_usuario = get_user_profile(usuario)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'actualizar_datos':
            usuario.email = request.POST.get('email')
            usuario.first_name = request.POST.get('first_name', '')
            usuario.last_name = request.POST.get('last_name', '')

            tipo_perfil = request.POST.get('tipo_perfil')
            if perfil_usuario:
                perfil_usuario.tipo_perfil = tipo_perfil
                perfil_usuario.save()

            usuario.save()
            messages.success(request, 'Datos actualizados correctamente')

        elif accion == 'cambiar_estado':
            if perfil_usuario:
                perfil_usuario.activo = not perfil_usuario.activo
                perfil_usuario.save()
                estado = 'activado' if perfil_usuario.activo else 'desactivado'
                messages.success(request, f'Usuario {estado} correctamente')

        elif accion == 'resetear_password':
            nueva_password = request.POST.get('nueva_password')
            if nueva_password:
                usuario.set_password(nueva_password)
                usuario.save()
                if perfil_usuario:
                    perfil_usuario.requiere_cambio_password = True
                    perfil_usuario.save()
                messages.success(request, 'Contraseña reseteada correctamente')

        return redirect('gestor_editar_usuario', user_id=user_id)

    context = {
        'perfil': perfil,
        'usuario_editado': usuario,
        'perfil_usuario': perfil_usuario,
    }
    return render(request, 'planes/usuarios/editar_usuario.html', context)


@login_required
def eliminar_usuario(request, user_id):
    """Vista para eliminar un usuario"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para eliminar usuarios')
        return redirect('dashboard_redirect')

    usuario = get_object_or_404(User, id=user_id)

    # No permitir eliminar superusuarios
    if usuario.is_superuser:
        messages.error(request, 'No se puede eliminar un superusuario')
        return redirect('gestor_lista_usuarios')

    # No permitir eliminar el propio usuario
    if usuario == request.user:
        messages.error(request, 'No puedes eliminarte a ti mismo')
        return redirect('gestor_lista_usuarios')

    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario {username} eliminado correctamente')
        return redirect('gestor_lista_usuarios')

    return redirect('gestor_lista_usuarios')


@login_required
def toggle_estado_usuario(request, user_id):
    """Vista para activar/desactivar un usuario"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para modificar usuarios')
        return redirect('dashboard_redirect')

    usuario = get_object_or_404(User, id=user_id)

    # No permitir desactivar superusuarios
    if usuario.is_superuser:
        messages.error(request, 'No se puede desactivar un superusuario')
        return redirect('gestor_lista_usuarios')

    # No permitir desactivar el propio usuario
    if usuario == request.user:
        messages.error(request, 'No puedes desactivarte a ti mismo')
        return redirect('gestor_lista_usuarios')

    if request.method == 'POST':
        perfil_usuario = get_user_profile(usuario)
        if perfil_usuario:
            perfil_usuario.activo = not perfil_usuario.activo
            perfil_usuario.save()

            # También actualizar el is_active del usuario de Django
            usuario.is_active = perfil_usuario.activo
            usuario.save()

            estado = 'activado' if perfil_usuario.activo else 'desactivado'
            messages.success(request, f'Usuario {usuario.username} {estado} correctamente')
        else:
            messages.error(request, 'No se pudo cambiar el estado del usuario')

    return redirect('gestor_lista_usuarios')


@login_required
def generar_credenciales_proveedor(request, proveedor_id):
    """Vista para generar credenciales de acceso para un proveedor"""
    perfil = get_user_profile(request.user)

    if not perfil.es_gestor:
        messages.error(request, 'No tiene permisos para generar credenciales')
        return redirect('dashboard_redirect')

    proveedor = get_object_or_404(Proveedor, id=proveedor_id)

    # Verificar que el proveedor no tenga usuario
    if proveedor.user is not None:
        messages.warning(request, f'El proveedor {proveedor.razon_social} ya tiene credenciales asignadas')
        return redirect('gestor_lista_usuarios')

    if request.method == 'POST':
        username = request.POST.get('username', proveedor.nit)
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Validar contraseñas
        if password != password_confirm:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'planes/usuarios/generar_credenciales.html', {
                'perfil': perfil,
                'proveedor': proveedor
            })

        # Validar que no exista el username
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Ya existe un usuario con el username {username}')
            return render(request, 'planes/usuarios/generar_credenciales.html', {
                'perfil': perfil,
                'proveedor': proveedor
            })

        try:
            with transaction.atomic():
                # Crear usuario Django
                user = User.objects.create_user(
                    username=username,
                    email=proveedor.email,
                    password=password,
                    first_name=proveedor.razon_social[:30],
                )

                # Crear perfil
                PerfilUsuario.objects.create(
                    user=user,
                    tipo_perfil='PROVEEDOR',
                    requiere_cambio_password=True,
                    activo=True
                )

                # Asociar usuario al proveedor
                proveedor.user = user
                proveedor.activo = True
                proveedor.save()

                messages.success(request,
                    f'Credenciales generadas exitosamente para {proveedor.razon_social}. '
                    f'Usuario: {username} - El proveedor deberá cambiar su contraseña en el primer acceso.')
                return redirect('gestor_lista_usuarios')

        except Exception as e:
            messages.error(request, f'Error al generar credenciales: {str(e)}')

    context = {
        'perfil': perfil,
        'proveedor': proveedor,
        'username_sugerido': proveedor.nit,
    }

    return render(request, 'planes/usuarios/generar_credenciales.html', context)