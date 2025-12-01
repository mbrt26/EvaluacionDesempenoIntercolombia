"""
Lógica de workflows y transiciones de estados para planes de mejoramiento
Basado en el diagrama de flujo de gestión de planes
"""
from django.utils import timezone
from datetime import timedelta


class PlanWorkflow:
    """Maneja las transiciones de estados y lógica de negocio del flujo"""

    # Matriz de transiciones permitidas
    TRANSICIONES_PERMITIDAS = {
        'BORRADOR': ['ENVIADO', 'PROCESO_FIRMAS'],
        'ENVIADO': ['PROCESO_FIRMAS', 'EN_REVISION'],

        # Flujo principal
        'PROCESO_FIRMAS': ['FIRMADO_ENVIADO', 'FALTA_ETICA'],
        'FIRMADO_ENVIADO': ['NO_RECIBIDO', 'ESPERANDO_APROBACION'],
        'ESPERANDO_APROBACION': ['SOLICITUD_AJUSTES', 'EN_RADICACION'],
        'EN_RADICACION': ['PM_RADICADO', 'RECHAZADO'],
        'PM_RADICADO': ['PM_REEVALUADO'],
        'PM_REEVALUADO': ['FIN'],

        # Flujo de excepciones
        'NO_RECIBIDO': ['ACLARACION', 'NO_RECIBIDO'],  # Puede permanecer en NO_RECIBIDO
        'ACLARACION': ['EP_REEVALUADO', 'ESPERANDO_APROBACION'],
        'EP_REEVALUADO': ['FIN'],
        'SOLICITUD_AJUSTES': ['ESPERANDO_APROBACION', 'EN_RADICACION'],
        'RECHAZADO': ['CANCELACION_RADICADA'],
        'CANCELACION_RADICADA': ['FIN'],
        'FALTA_ETICA': ['FIN'],

        # Estados legacy
        'EN_REVISION': ['REQUIERE_AJUSTES', 'APROBADO', 'RECHAZADO'],
        'REQUIERE_AJUSTES': ['ENVIADO'],
        'APROBADO': ['FIN'],
        'DOCUMENTOS_REEVALUADOS': ['FIN'],
    }

    # Roles permitidos para cada transición
    PERMISOS_TRANSICION = {
        'BORRADOR -> PROCESO_FIRMAS': ['PROVEEDOR'],
        'PROCESO_FIRMAS -> FIRMADO_ENVIADO': ['PROVEEDOR'],
        'FIRMADO_ENVIADO -> ESPERANDO_APROBACION': ['TECNICO', 'GESTOR'],
        'FIRMADO_ENVIADO -> NO_RECIBIDO': ['SISTEMA'],  # Automático después de 30 días
        'NO_RECIBIDO -> ACLARACION': ['TECNICO', 'GESTOR'],
        'ACLARACION -> ESPERANDO_APROBACION': ['PROVEEDOR'],
        'ACLARACION -> EP_REEVALUADO': ['SISTEMA'],  # Integración con app externa
        'ESPERANDO_APROBACION -> SOLICITUD_AJUSTES': ['TECNICO', 'GESTOR'],
        'ESPERANDO_APROBACION -> EN_RADICACION': ['TECNICO', 'GESTOR'],
        'SOLICITUD_AJUSTES -> ESPERANDO_APROBACION': ['PROVEEDOR'],
        'EN_RADICACION -> PM_RADICADO': ['GESTOR_COMPRAS'],
        'EN_RADICACION -> RECHAZADO': ['GESTOR_COMPRAS'],
        'RECHAZADO -> CANCELACION_RADICADA': ['GESTOR_COMPRAS'],
        'PM_RADICADO -> PM_REEVALUADO': ['SISTEMA'],  # Integración con app externa
        'PROCESO_FIRMAS -> FALTA_ETICA': ['GESTOR'],  # Si proveedor es suspendido
    }

    @staticmethod
    def puede_transicionar(estado_actual, estado_nuevo):
        """
        Verifica si una transición de estado es válida
        """
        estados_permitidos = PlanWorkflow.TRANSICIONES_PERMITIDAS.get(estado_actual, [])
        return estado_nuevo in estados_permitidos

    @staticmethod
    def tiene_permiso(usuario, estado_actual, estado_nuevo):
        """
        Verifica si un usuario tiene permiso para realizar una transición
        """
        clave_transicion = f'{estado_actual} -> {estado_nuevo}'
        roles_permitidos = PlanWorkflow.PERMISOS_TRANSICION.get(clave_transicion, [])

        # Si no hay permisos definidos, denegar por defecto
        if not roles_permitidos:
            return False

        # Verificar rol del usuario
        if hasattr(usuario, 'perfil'):
            tipo_perfil = usuario.perfil.tipo_perfil
            return tipo_perfil in roles_permitidos
        elif hasattr(usuario, 'proveedor'):
            return 'PROVEEDOR' in roles_permitidos

        return False

    @staticmethod
    def calcular_dias_sin_respuesta(plan):
        """
        Calcula los días transcurridos sin respuesta desde el envío de la carta
        """
        if plan.fecha_carta and plan.estado == 'FIRMADO_ENVIADO':
            dias = (timezone.now() - plan.fecha_carta).days
            return dias
        return 0

    @staticmethod
    def requiere_accion_automatica(plan):
        """
        Verifica si el plan requiere una acción automática del sistema
        """
        # Si pasaron 30 días sin recibir el plan, cambiar a NO_RECIBIDO
        if plan.estado == 'FIRMADO_ENVIADO':
            dias_sin_respuesta = PlanWorkflow.calcular_dias_sin_respuesta(plan)
            if dias_sin_respuesta >= 30:
                return ('NO_RECIBIDO', 'Pasaron 30 días sin recibir el plan')

        return None

    @staticmethod
    def transicionar(plan, nuevo_estado, usuario=None, comentario='', **kwargs):
        """
        Realiza una transición de estado con validaciones y actualizaciones

        Args:
            plan: Instancia de PlanMejoramiento
            nuevo_estado: Estado al que se quiere transicionar
            usuario: Usuario que realiza la transición (opcional para acciones del sistema)
            comentario: Comentario sobre la transición
            **kwargs: Argumentos adicionales según el estado (ej: numero_radicado, motivo_rechazo)

        Returns:
            (success: bool, message: str)
        """
        from planes.models import HistorialEstado

        estado_anterior = plan.estado

        # Validar que la transición sea válida
        if not PlanWorkflow.puede_transicionar(estado_anterior, nuevo_estado):
            return False, f'No se puede cambiar de {estado_anterior} a {nuevo_estado}'

        # Validar permisos (si hay usuario)
        if usuario and not PlanWorkflow.tiene_permiso(usuario, estado_anterior, nuevo_estado):
            return False, 'No tiene permisos para realizar esta transición'

        # Actualizar estado
        plan.estado = nuevo_estado

        # Actualizar campos específicos según el nuevo estado
        if nuevo_estado == 'PROCESO_FIRMAS':
            plan.fecha_carta = timezone.now()
            if kwargs.get('carta_evaluacion'):
                plan.carta_evaluacion = kwargs['carta_evaluacion']

        elif nuevo_estado == 'FIRMADO_ENVIADO':
            plan.fecha_envio = timezone.now()

        elif nuevo_estado == 'NO_RECIBIDO':
            plan.dias_sin_respuesta = PlanWorkflow.calcular_dias_sin_respuesta(plan)

        elif nuevo_estado == 'ACLARACION':
            plan.fecha_aclaracion = timezone.now()
            if kwargs.get('observaciones_aclaracion'):
                plan.observaciones_aclaracion = kwargs['observaciones_aclaracion']

        elif nuevo_estado == 'EN_RADICACION':
            plan.fecha_revision = timezone.now()
            if usuario:
                plan.revisado_por = usuario

        elif nuevo_estado == 'PM_RADICADO':
            plan.numero_radicado = kwargs.get('numero_radicado', '')
            plan.fecha_radicacion = timezone.now()

        elif nuevo_estado == 'RECHAZADO':
            plan.motivo_rechazo = kwargs.get('motivo_rechazo', '')
            plan.fecha_revision = timezone.now()
            if usuario:
                plan.revisado_por = usuario

        elif nuevo_estado == 'CANCELACION_RADICADA':
            plan.fecha_revision = timezone.now()

        elif nuevo_estado == 'FALTA_ETICA':
            plan.proveedor_suspendido = True
            plan.fecha_suspension = timezone.now().date()

        elif nuevo_estado in ['PM_REEVALUADO', 'EP_REEVALUADO', 'FIN']:
            # Estados finales - marcar como completado
            if not plan.fecha_aprobacion:
                plan.fecha_aprobacion = timezone.now()

        # Guardar el plan
        plan.save()

        # Crear registro en historial
        HistorialEstado.objects.create(
            plan=plan,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            usuario=usuario,
            comentario=comentario or f'Transición de {estado_anterior} a {nuevo_estado}'
        )

        return True, f'Estado cambiado exitosamente a {nuevo_estado}'

    @staticmethod
    def obtener_proximos_estados(plan, usuario=None):
        """
        Obtiene los estados a los que se puede transicionar desde el estado actual

        Args:
            plan: Instancia de PlanMejoramiento
            usuario: Usuario actual (opcional, para filtrar por permisos)

        Returns:
            Lista de tuplas (codigo_estado, nombre_estado)
        """
        from planes.models import PlanMejoramiento

        estados_posibles = PlanWorkflow.TRANSICIONES_PERMITIDAS.get(plan.estado, [])

        # Si hay usuario, filtrar por permisos
        if usuario:
            estados_filtrados = []
            for estado in estados_posibles:
                if PlanWorkflow.tiene_permiso(usuario, plan.estado, estado):
                    estados_filtrados.append(estado)
            estados_posibles = estados_filtrados

        # Convertir códigos a tuplas (codigo, nombre)
        estados_dict = dict(PlanMejoramiento.ESTADOS)
        return [(codigo, estados_dict.get(codigo, codigo)) for codigo in estados_posibles]

    @staticmethod
    def es_estado_final(estado):
        """Verifica si un estado es final (no tiene transiciones)"""
        return estado == 'FIN'

    @staticmethod
    def es_estado_activo(estado):
        """Verifica si un plan está en un estado activo (requiere seguimiento)"""
        estados_activos = [
            'PROCESO_FIRMAS', 'FIRMADO_ENVIADO', 'NO_RECIBIDO', 'ACLARACION',
            'ESPERANDO_APROBACION', 'SOLICITUD_AJUSTES', 'EN_RADICACION'
        ]
        return estado in estados_activos

    @staticmethod
    def obtener_tipo_flujo(estado):
        """
        Retorna el tipo de flujo al que pertenece el estado
        Returns: 'principal', 'excepcion', 'legacy', 'final'
        """
        flujo_principal = [
            'PROCESO_FIRMAS', 'FIRMADO_ENVIADO', 'ESPERANDO_APROBACION',
            'EN_RADICACION', 'PM_RADICADO', 'PM_REEVALUADO'
        ]
        flujo_excepcion = [
            'NO_RECIBIDO', 'ACLARACION', 'EP_REEVALUADO', 'SOLICITUD_AJUSTES',
            'RECHAZADO', 'CANCELACION_RADICADA', 'FALTA_ETICA'
        ]
        estados_legacy = [
            'EN_REVISION', 'REQUIERE_AJUSTES', 'APROBADO', 'DOCUMENTOS_REEVALUADOS'
        ]

        if estado in flujo_principal:
            return 'principal'
        elif estado in flujo_excepcion:
            return 'excepcion'
        elif estado in estados_legacy:
            return 'legacy'
        elif estado == 'FIN':
            return 'final'
        else:
            return 'inicial'
