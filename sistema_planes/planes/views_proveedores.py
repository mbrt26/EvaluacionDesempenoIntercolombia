"""
Vista nueva para lista de proveedores - Creada desde cero
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Proveedor, Evaluacion, PlanMejoramiento

@login_required
def lista_proveedores_nueva(request):
    """Vista completamente nueva para proveedores"""

    # Verificar permisos
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos para ver esta página')
        return redirect('dashboard_proveedor')

    # Obtener filtros
    filtro_proveedor = request.GET.get('proveedor', '')
    filtro_categoria = request.GET.get('categoria', '')
    filtro_estado_plan = request.GET.get('estado_plan', '')
    filtro_requiere_plan = request.GET.get('requiere_plan', '')

    # Obtener todos los datos necesarios
    datos_proveedores = []

    # Obtener todos los proveedores con sus evaluaciones
    proveedores = Proveedor.objects.all()

    # Aplicar filtro de proveedor
    if filtro_proveedor:
        proveedores = proveedores.filter(
            Q(razon_social__icontains=filtro_proveedor) |
            Q(nit__icontains=filtro_proveedor)
        )

    proveedores = proveedores.order_by('razon_social')
    
    for proveedor in proveedores:
        # Obtener la última evaluación
        evaluacion = Evaluacion.objects.filter(
            proveedor=proveedor
        ).order_by('-fecha').first()
        
        if evaluacion:
            # Obtener el plan si existe
            plan = PlanMejoramiento.objects.filter(
                proveedor=proveedor,
                evaluacion=evaluacion
            ).order_by('-fecha_creacion').first()
            
            # Determinar el estado del plan
            estado_plan = "NO_APLICA"
            color_estado = "gris"
            icono_estado = "○"
            
            if evaluacion.puntaje < 80:
                if plan:
                    estado_plan = plan.get_estado_display()
                    if plan.estado == 'APROBADO':
                        color_estado = "verde"
                        icono_estado = "✓"
                    elif plan.estado == 'RECHAZADO':
                        color_estado = "rojo"
                        icono_estado = "✗"
                    elif plan.estado == 'ENVIADO':
                        color_estado = "azul"
                        icono_estado = "→"
                    elif plan.estado == 'REQUIERE_AJUSTES':
                        color_estado = "naranja"
                        icono_estado = "!"
                    else:
                        color_estado = "amarillo"
                        icono_estado = "..."
                else:
                    estado_plan = "SIN PLAN (Requerido)"
                    color_estado = "rojo"
                    icono_estado = "⚠"
            else:
                estado_plan = "No requiere"
                color_estado = "verde-claro"
                icono_estado = "—"

            # Determinar color del puntaje (Parametrización ITCO-ISA)
            if evaluacion.puntaje >= 80:
                color_puntaje = "verde"
            elif evaluacion.puntaje >= 60:
                color_puntaje = "amarillo"
            else:
                color_puntaje = "rojo"

            datos_proveedores.append({
                'proveedor': proveedor,
                'evaluacion': evaluacion,
                'plan': plan,
                'estado_plan': estado_plan,
                'color_estado': color_estado,
                'icono_estado': icono_estado,
                'color_puntaje': color_puntaje,
                'requiere_plan': evaluacion.puntaje < 80,
            })

    # Aplicar filtros adicionales
    datos_filtrados = datos_proveedores

    # Filtro por categoría de puntaje
    if filtro_categoria:
        if filtro_categoria == 'critica':
            datos_filtrados = [d for d in datos_filtrados if d['evaluacion'].puntaje < 60]
        elif filtro_categoria == 'aceptable':
            datos_filtrados = [d for d in datos_filtrados if 60 <= d['evaluacion'].puntaje < 80]
        elif filtro_categoria == 'satisfactoria':
            datos_filtrados = [d for d in datos_filtrados if d['evaluacion'].puntaje >= 80]

    # Filtro por estado del plan
    if filtro_estado_plan:
        if filtro_estado_plan == 'SIN_PLAN':
            datos_filtrados = [d for d in datos_filtrados if d['requiere_plan'] and not d['plan']]
        elif filtro_estado_plan == 'NO_REQUIERE':
            datos_filtrados = [d for d in datos_filtrados if not d['requiere_plan']]
        else:
            datos_filtrados = [d for d in datos_filtrados if d['plan'] and d['plan'].estado == filtro_estado_plan]

    # Filtro por si requiere plan
    if filtro_requiere_plan:
        if filtro_requiere_plan == 'si':
            datos_filtrados = [d for d in datos_filtrados if d['requiere_plan']]
        elif filtro_requiere_plan == 'no':
            datos_filtrados = [d for d in datos_filtrados if not d['requiere_plan']]

    # Ordenar por jerarquía: Críticos primero (puntaje bajo), luego aceptables, luego satisfactorios
    # Orden: 1) Puntaje ascendente (peores primero), 2) Razón social alfabética
    datos_filtrados.sort(key=lambda x: (x['evaluacion'].puntaje, x['proveedor'].razon_social))

    # Calcular estadísticas (siempre sobre todos los datos, no solo filtrados)
    total = len(datos_proveedores)
    requieren_plan = sum(1 for d in datos_proveedores if d['requiere_plan'])
    con_plan_aprobado = sum(1 for d in datos_proveedores if d['plan'] and d['plan'].estado == 'APROBADO')
    con_plan_pendiente = sum(1 for d in datos_proveedores if d['plan'] and d['plan'].estado in ['ENVIADO', 'EN_REVISION'])

    context = {
        'datos': datos_filtrados,
        'filtros': {
            'proveedor': filtro_proveedor,
            'categoria': filtro_categoria,
            'estado_plan': filtro_estado_plan,
            'requiere_plan': filtro_requiere_plan,
        },
        'estadisticas': {
            'total': total,
            'requieren_plan': requieren_plan,
            'aprobados': con_plan_aprobado,
            'pendientes': con_plan_pendiente,
        }
    }

    return render(request, 'planes/proveedores_minimal.html', context)


@login_required
def crear_proveedor(request):
    """Vista para crear un nuevo proveedor"""
    
    # Verificar que NO sea proveedor (solo técnicos pueden crear proveedores)
    if hasattr(request.user, 'proveedor'):
        messages.error(request, 'No tiene permisos para crear proveedores')
        return redirect('dashboard_proveedor')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        nit = request.POST.get('nit')
        razon_social = request.POST.get('razon_social')
        email = request.POST.get('email')
        email_adicional = request.POST.get('email_adicional', '')  # Campo opcional

        # Validar que no exista el NIT
        if Proveedor.objects.filter(nit=nit).exists():
            messages.error(request, f'Ya existe un proveedor con NIT {nit}')
            return redirect('crear_proveedor')

        try:
            # Crear proveedor SIN usuario (será creado por el gestor)
            proveedor = Proveedor.objects.create(
                user=None,  # Sin usuario inicialmente
                nit=nit,
                razon_social=razon_social,
                email=email,
                email_adicional=email_adicional if email_adicional else None,
                activo=False  # Inactivo hasta que el gestor genere credenciales
            )

            messages.success(request,
                f'Proveedor {razon_social} registrado exitosamente. '
                f'El Gestor debe generar las credenciales de acceso desde el módulo de usuarios.')
            return redirect('tecnico_proveedores')

        except Exception as e:
            messages.error(request, f'Error al crear proveedor: {str(e)}')
            return redirect('crear_proveedor')

    return render(request, 'planes/crear_proveedor.html')