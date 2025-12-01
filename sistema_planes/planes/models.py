"""
Modelos de datos para el sistema de planes de mejoramiento
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta


class PerfilUsuario(models.Model):
    """Modelo para los diferentes perfiles de usuario en el sistema"""
    TIPOS_PERFIL = [
        ('TECNICO', 'Técnico'),
        ('PROVEEDOR', 'Proveedor'),
        ('GESTOR', 'Gestor de Planes de Mejoramiento'),
        ('GESTOR_COMPRAS', 'Gestor de Compras'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_perfil = models.CharField(max_length=20, choices=TIPOS_PERFIL, default='PROVEEDOR')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    requiere_cambio_password = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_perfil_display()}"

    @property
    def es_tecnico(self):
        return self.tipo_perfil == 'TECNICO'

    @property
    def es_proveedor(self):
        return self.tipo_perfil == 'PROVEEDOR'

    @property
    def es_gestor(self):
        return self.tipo_perfil == 'GESTOR'

    @property
    def es_gestor_compras(self):
        return self.tipo_perfil == 'GESTOR_COMPRAS'


class Proveedor(models.Model):
    """Modelo para los proveedores"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='proveedor', null=True, blank=True)
    nit = models.CharField(max_length=20, unique=True, verbose_name='NIT')
    razon_social = models.CharField(max_length=200, verbose_name='Razón Social')
    email = models.EmailField(verbose_name='Email')
    email_adicional = models.EmailField(blank=True, null=True, verbose_name='Email Adicional del Gestor del Proyecto')
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['razon_social']
    
    def __str__(self):
        return f"{self.nit} - {self.razon_social}"


class Evaluacion(models.Model):
    """Modelo para las evaluaciones de desempeño"""
    TIPOS_CONTRATO = [
        # Genéricos
        ('OBRA', 'Obra'),
        ('SUMINISTRO', 'Suministro'),
        ('SERVICIO', 'Prestación de Servicios'),
        ('CONSULTORIA', 'Consultoría'),
        ('INTERVENTORIA', 'Interventoría'),
        ('ORDEN_COMPRA', 'Orden de Compra'),
        # Sector Eléctrico
        ('OBRAS_CIVILES', 'Obras Civiles'),
        ('SUMINISTRO_EQUIPOS', 'Suministro de Equipos'),
        ('MONTAJE_ELECTROMECANICO', 'Montaje Electromecánico'),
        ('SERVICIOS_TECNICOS', 'Servicios Técnicos Especializados'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('ESTUDIOS_DISENOS', 'Estudios y Diseños'),
        ('TRANSPORTE', 'Transporte'),
        ('OTRO', 'Otro'),
    ]

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='evaluaciones'
    )
    periodo = models.CharField(max_length=50, verbose_name='Período', blank=True, null=True)
    numero_contrato = models.CharField(max_length=100, verbose_name='N° Contrato/Orden', blank=True, null=True)
    tipo_contrato = models.CharField(max_length=30, choices=TIPOS_CONTRATO, verbose_name='Tipo de Contrato', blank=True, null=True)
    subcategoria = models.CharField(max_length=200, verbose_name='Subcategoría', blank=True, null=True)
    tecnico_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluaciones_asignadas',
        verbose_name='Técnico Asignado'
    )
    puntaje = models.IntegerField(verbose_name='Puntaje')
    fecha = models.DateField(verbose_name='Fecha de Evaluación')
    fecha_limite_aclaracion = models.DateField(verbose_name='Fecha Límite de Aclaración', null=True, blank=True)
    fecha_limite_plan = models.DateField(verbose_name='Fecha Límite Plan', null=True, blank=True)
    
    # Desglose del puntaje - Ajustado según documento
    puntaje_gestion = models.IntegerField(default=0, verbose_name='Gestión')
    puntaje_calidad = models.IntegerField(default=0, verbose_name='Calidad')
    puntaje_oportunidad = models.IntegerField(default=0, verbose_name='Oportunidad')
    puntaje_ambiental_social = models.IntegerField(default=0, verbose_name='Ambiental y Social')
    puntaje_sst = models.IntegerField(default=0, verbose_name='Seguridad y Salud en el Trabajo')
    
    # Puntajes máximos por criterio (varían según tipo de contrato)
    max_gestion = models.IntegerField(default=25, verbose_name='Máximo Gestión')
    max_calidad = models.IntegerField(default=25, verbose_name='Máximo Calidad')
    max_oportunidad = models.IntegerField(default=25, verbose_name='Máximo Oportunidad')
    max_ambiental_social = models.IntegerField(default=25, verbose_name='Máximo Ambiental y Social')
    max_sst = models.IntegerField(default=25, verbose_name='Máximo SST')
    
    # Campos de aprobación
    requiere_aprobacion_sst = models.BooleanField(default=False, verbose_name='Requiere Aprobación SST')
    requiere_aprobacion_ambiental = models.BooleanField(default=False, verbose_name='Requiere Aprobación Ambiental')
    
    # Observaciones por criterio
    observaciones_gestion = models.TextField(blank=True, verbose_name='Observaciones Gestión')
    observaciones_calidad = models.TextField(blank=True, verbose_name='Observaciones Calidad')
    observaciones_oportunidad = models.TextField(blank=True, verbose_name='Observaciones Oportunidad')
    observaciones_ambiental_social = models.TextField(blank=True, verbose_name='Observaciones Ambiental y Social')
    observaciones_sst = models.TextField(blank=True, verbose_name='Observaciones SST')
    observaciones_generales = models.TextField(blank=True, verbose_name='Observaciones Generales')
    
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    # Campos para proceso de firmas
    ESTADOS_FIRMA = [
        ('PROCESO_FIRMAS', 'Proceso de Firmas'),
        ('FIRMADO', 'Firmado y Enviado'),
        ('CANCELADO', 'Cancelado'),
        ('CAMBIO_NOTAS', 'Cambio de Notas'),
    ]

    estado_firma = models.CharField(
        max_length=20,
        choices=ESTADOS_FIRMA,
        default='PROCESO_FIRMAS',
        verbose_name='Estado del Proceso de Firmas'
    )
    fecha_cambio_estado_firma = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Cambio de Estado de Firma'
    )
    observaciones_firma = models.TextField(
        blank=True,
        verbose_name='Observaciones del Proceso de Firmas'
    )
    fecha_envio_notificacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Envío de Notificación al Proveedor'
    )
    resumen_notificacion = models.TextField(
        blank=True,
        verbose_name='Resumen de la Notificación Enviada'
    )

    # Campos para el flujo de evaluación (bifurcaciones después del envío)
    ESTADOS_FLUJO = [
        ('FLUJO_NORMAL', 'Flujo Normal'),
        ('FALTA_ETICA', 'Falta de Ética'),
        ('ACLARACION', 'Aclaración Solicitada'),
        ('REEVALUADO', 'Reevaluado'),
    ]

    estado_flujo_evaluacion = models.CharField(
        max_length=20,
        choices=ESTADOS_FLUJO,
        default='FLUJO_NORMAL',
        verbose_name='Estado del Flujo de Evaluación'
    )
    fecha_cambio_estado_flujo = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Cambio de Estado de Flujo'
    )
    observaciones_flujo = models.TextField(
        blank=True,
        verbose_name='Observaciones del Flujo de Evaluación'
    )
    # Para reevaluaciones
    puntaje_reevaluacion = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Puntaje de Reevaluación'
    )
    fecha_reevaluacion = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Reevaluación'
    )

    class Meta:
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        unique_together = ['proveedor', 'periodo']
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.proveedor.razon_social} - {self.periodo} - {self.puntaje}/100"
    
    def requiere_plan(self):
        """Determina si requiere plan de mejoramiento"""
        return self.puntaje < 80
    
    @property
    def estado_evaluacion(self):
        """Retorna el estado según el puntaje (Parametrización ITCO-ISA)"""
        if self.puntaje >= 80:
            return 'Desempeño Satisfactorio'
        elif self.puntaje >= 60:
            return 'Desempeño Aceptable'
        else:
            return 'Desempeño Crítico'


class PlanMejoramiento(models.Model):
    """Modelo para los planes de mejoramiento"""
    ESTADOS = [
        # Estados iniciales
        ('BORRADOR', 'Borrador'),
        ('ENVIADO', 'Enviado'),

        # Flujo principal (azul - camino exitoso)
        ('PROCESO_FIRMAS', 'Proceso de Firmas'),
        ('FIRMADO_ENVIADO', 'Firmado y Enviado'),
        ('ESPERANDO_APROBACION', 'Esperando Aprobación'),
        ('EN_RADICACION', 'En Radicación'),
        ('PM_RADICADO', 'PM Radicado'),
        ('PM_REEVALUADO', 'PM Reevaluado'),

        # Flujo de excepciones (gris - alternativas)
        ('NO_RECIBIDO', 'No Recibido'),
        ('ACLARACION', 'Aclaración'),
        ('EP_REEVALUADO', 'EP Reevaluado'),
        ('SOLICITUD_AJUSTES', 'Solicitud de Ajustes'),
        ('REQUIERE_AJUSTES', 'Requiere Ajustes'),
        ('RECHAZADO', 'Rechazado'),
        ('CANCELACION_RADICADA', 'Cancelación Radicada'),
        ('FALTA_ETICA', 'Falta de Ética'),

        # Estados legacy (mantener compatibilidad)
        ('EN_REVISION', 'En Revisión'),
        ('DOCUMENTOS_REEVALUADOS', 'Documentos Reevaluados'),
        ('APROBADO', 'Aprobado'),

        # Estado final
        ('FIN', 'Fin'),
    ]
    
    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name='planes'
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='planes_mejoramiento'
    )
    estado = models.CharField(
        max_length=30,
        choices=ESTADOS,
        default='BORRADOR',
        verbose_name='Estado'
    )
    
    # Contenido del plan
    analisis_causa = models.TextField(verbose_name='Análisis de Causa Raíz')
    acciones_propuestas = models.TextField(verbose_name='Acciones Propuestas')
    responsable = models.CharField(max_length=200, verbose_name='Responsable')
    fecha_implementacion = models.DateField(verbose_name='Fecha de Implementación')
    indicadores_seguimiento = models.TextField(verbose_name='Indicadores de Seguimiento')

    # Archivos adjuntos del plan
    archivo_analisis_causa = models.FileField(
        upload_to='planes_mejoramiento/analisis/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Archivo Análisis de Causa Raíz'
    )
    archivo_acciones_propuestas = models.FileField(
        upload_to='planes_mejoramiento/acciones/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Archivo Acciones Propuestas'
    )
    archivo_indicadores = models.FileField(
        upload_to='planes_mejoramiento/indicadores/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Archivo Indicadores de Seguimiento'
    )
    archivo_otros = models.FileField(
        upload_to='planes_mejoramiento/otros/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Otros Archivos Adjuntos'
    )

    # Metadata
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    
    # Revisión del técnico
    comentarios_tecnico = models.TextField(blank=True, verbose_name='Comentarios del Técnico')
    fecha_revision = models.DateTimeField(null=True, blank=True)
    revisado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planes_revisados'
    )
    
    # Historial
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    numero_version = models.IntegerField(default=1)

    # Nuevos campos para flujo completo
    numero_radicado = models.CharField(max_length=100, blank=True, null=True, verbose_name='Número de Radicado')
    fecha_radicacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Radicación')
    carta_evaluacion = models.FileField(upload_to='cartas_evaluacion/%Y/%m/', null=True, blank=True, verbose_name='Carta de Evaluación CS')
    fecha_carta = models.DateTimeField(null=True, blank=True, verbose_name='Fecha Envío Carta')
    dias_sin_respuesta = models.IntegerField(default=0, verbose_name='Días sin Respuesta')
    proveedor_suspendido = models.BooleanField(default=False, verbose_name='Proveedor Suspendido por Falta de Ética')
    fecha_suspension = models.DateField(null=True, blank=True, verbose_name='Fecha de Suspensión')
    motivo_rechazo = models.TextField(blank=True, verbose_name='Motivo de Rechazo')
    fecha_aclaracion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Aclaración')
    observaciones_aclaracion = models.TextField(blank=True, verbose_name='Observaciones de Aclaración')
    
    class Meta:
        verbose_name = 'Plan de Mejoramiento'
        verbose_name_plural = 'Planes de Mejoramiento'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Plan {self.proveedor.razon_social} - {self.get_estado_display()}"
    
    def save(self, *args, **kwargs):
        # Establecer fecha límite si no existe (20 días hábiles)
        if not self.fecha_limite and self.evaluacion:
            self.fecha_limite = date.today() + timedelta(days=30)
        
        # Si se envía, actualizar fecha de envío
        if self.estado == 'ENVIADO' and not self.fecha_envio:
            self.fecha_envio = timezone.now()
        
        # Si se aprueba, actualizar fecha de aprobación
        if self.estado == 'APROBADO' and not self.fecha_aprobacion:
            self.fecha_aprobacion = timezone.now()
            
        super().save(*args, **kwargs)
    
    @property
    def dias_pendiente(self):
        """Calcula días desde el envío"""
        if self.fecha_envio:
            return (date.today() - self.fecha_envio.date()).days
        return 0
    
    @property
    def dias_para_vencimiento(self):
        """Calcula días hasta el vencimiento"""
        if self.fecha_limite:
            dias = (self.fecha_limite - date.today()).days
            return max(0, dias)
        return None
    
    @property
    def esta_vencido(self):
        """Verifica si el plan está vencido"""
        if self.fecha_limite and self.estado not in ['APROBADO', 'RECHAZADO']:
            return date.today() > self.fecha_limite
        return False


class DocumentoPlan(models.Model):
    """Modelo para los documentos adjuntos al plan"""
    plan = models.ForeignKey(
        PlanMejoramiento,
        on_delete=models.CASCADE,
        related_name='documentos'
    )
    archivo = models.FileField(
        upload_to='planes/documentos/%Y/%m/',
        verbose_name='Archivo'
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Documento')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    fecha_carga = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Documento del Plan'
        verbose_name_plural = 'Documentos del Plan'
        ordering = ['-fecha_carga']
    
    def __str__(self):
        return f"{self.nombre} - {self.plan.proveedor.razon_social}"


class AccionMejora(models.Model):
    """Modelo para las acciones específicas de mejora"""
    plan = models.ForeignKey(
        PlanMejoramiento,
        on_delete=models.CASCADE,
        related_name='acciones'
    )
    descripcion = models.TextField(verbose_name='Descripción de la Acción')
    responsable = models.CharField(max_length=200, verbose_name='Responsable')
    fecha_compromiso = models.DateField(verbose_name='Fecha Compromiso')
    indicador = models.CharField(max_length=500, verbose_name='Indicador de Éxito')
    completado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Acción de Mejora'
        verbose_name_plural = 'Acciones de Mejora'
        ordering = ['fecha_compromiso']
    
    def __str__(self):
        return f"{self.descripcion[:50]}... - {self.fecha_compromiso}"


class HistorialEstado(models.Model):
    """Modelo para el historial de cambios de estado"""
    plan = models.ForeignKey(
        PlanMejoramiento,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    estado_anterior = models.CharField(max_length=30, verbose_name='Estado Anterior')
    estado_nuevo = models.CharField(max_length=30, verbose_name='Estado Nuevo')
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario que realizó el cambio'
    )
    comentario = models.TextField(blank=True, verbose_name='Comentario')
    
    class Meta:
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historial de Estados'
        ordering = ['-fecha_cambio']
    
    def __str__(self):
        return f"{self.plan} - {self.estado_anterior} → {self.estado_nuevo}"


class HistorialCambioCampo(models.Model):
    """Modelo para el historial de cambios en campos específicos del plan"""
    plan = models.ForeignKey(
        PlanMejoramiento,
        on_delete=models.CASCADE,
        related_name='historial_cambios_campos'
    )
    campo = models.CharField(max_length=100, verbose_name='Campo modificado')
    valor_anterior = models.TextField(blank=True, null=True, verbose_name='Valor anterior')
    valor_nuevo = models.TextField(blank=True, null=True, verbose_name='Valor nuevo')
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario que realizó el cambio'
    )

    class Meta:
        verbose_name = 'Historial de Cambio de Campo'
        verbose_name_plural = 'Historial de Cambios de Campos'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.plan} - Campo: {self.campo} ({self.fecha_cambio.strftime('%d/%m/%Y %H:%M')})"


class PlanAdjunto(models.Model):
    """Modelo para los archivos adjuntos de un plan de mejoramiento"""
    TIPOS_DOCUMENTO = [
        ('PLAN_MEJORAMIENTO', 'Plan de Mejoramiento'),
        ('ANALISIS_CAUSA_RAIZ', 'Análisis de Causa Raíz'),
        ('OTRO', 'Otro'),
    ]

    plan = models.ForeignKey(
        PlanMejoramiento,
        on_delete=models.CASCADE,
        related_name='adjuntos',
        verbose_name='Plan de Mejoramiento'
    )
    tipo_documento = models.CharField(
        max_length=30,
        choices=TIPOS_DOCUMENTO,
        default='OTRO',
        verbose_name='Tipo de Documento'
    )
    archivo = models.FileField(
        upload_to='planes_adjuntos/%Y/%m/',
        verbose_name='Archivo'
    )
    nombre_original = models.CharField(
        max_length=255,
        verbose_name='Nombre del Archivo',
        blank=True
    )
    descripcion = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Descripción'
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Subido por'
    )

    class Meta:
        verbose_name = 'Adjunto del Plan'
        verbose_name_plural = 'Adjuntos del Plan'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.nombre_original}"

    def save(self, *args, **kwargs):
        if not self.nombre_original and self.archivo:
            self.nombre_original = self.archivo.name
        super().save(*args, **kwargs)


class TipoCalificacion(models.Model):
    """Tipos de calificación según Excel SAP"""
    codigo = models.CharField(max_length=100, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Calificación'
        verbose_name_plural = 'Tipos de Calificación'
        ordering = ['codigo']

    def __str__(self):
        return self.nombre


class CriterioEvaluacion(models.Model):
    """
    Criterios de evaluación según parametrización SAP
    Basado en el archivo: Ponderacion Evaluacion en SAP (1).xlsx
    """
    # Campos del Excel
    id_sap = models.IntegerField(verbose_name='ID SAP')
    descripcion_criterio = models.CharField(max_length=500, verbose_name='Descripción del Criterio')
    id_criterio = models.IntegerField(verbose_name='ID Criterio')
    respuesta_normal = models.TextField(verbose_name='Respuesta Normal')
    respuesta_corta = models.CharField(max_length=500, verbose_name='Respuesta Corta')
    sociedad = models.CharField(max_length=50, verbose_name='Sociedad', default='ISA')
    tipo_calificacion = models.ForeignKey(
        TipoCalificacion,
        on_delete=models.CASCADE,
        related_name='criterios',
        verbose_name='Tipo de Calificación'
    )
    puntuacion_maxima = models.IntegerField(verbose_name='Puntuación Máxima')

    # Campos adicionales para organización
    orden = models.IntegerField(default=0, verbose_name='Orden de Presentación')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Criterio de Evaluación'
        verbose_name_plural = 'Criterios de Evaluación'
        ordering = ['tipo_calificacion', 'id_criterio', 'orden']
        unique_together = ['id_sap', 'tipo_calificacion', 'id_criterio', 'puntuacion_maxima', 'sociedad']

    def __str__(self):
        return f"{self.descripcion_criterio} - {self.puntuacion_maxima} pts"


class RespuestaEvaluacion(models.Model):
    """
    Guarda las respuestas seleccionadas para cada criterio en una evaluación
    """
    evaluacion = models.ForeignKey(
        'Evaluacion',
        on_delete=models.CASCADE,
        related_name='respuestas',
        verbose_name='Evaluación'
    )
    criterio = models.ForeignKey(
        CriterioEvaluacion,
        on_delete=models.CASCADE,
        related_name='respuestas',
        verbose_name='Criterio Seleccionado'
    )
    id_criterio = models.IntegerField(verbose_name='ID Criterio')
    puntuacion_obtenida = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Puntuación Obtenida'
    )
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Respuesta de Evaluación'
        verbose_name_plural = 'Respuestas de Evaluación'
        unique_together = ['evaluacion', 'id_criterio']
        ordering = ['evaluacion', 'id_criterio']

    def __str__(self):
        return f"{self.evaluacion.id} - {self.criterio.descripcion_criterio}: {self.puntuacion_obtenida} pts"


class Notificacion(models.Model):
    """Modelo para notificaciones del sistema"""
    TIPOS = [
        ('PLAN_ENVIADO', 'Plan Enviado'),
        ('PLAN_REVISADO', 'Plan Revisado'),
        ('PLAN_APROBADO', 'Plan Aprobado'),
        ('PLAN_RECHAZADO', 'Plan Rechazado'),
        ('PLAN_REQUIERE_AJUSTES', 'Plan Requiere Ajustes'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Usuario'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TIPOS,
        verbose_name='Tipo'
    )
    plan = models.ForeignKey(
        PlanMejoramiento,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name='Plan',
        null=True,
        blank=True
    )
    mensaje = models.TextField(verbose_name='Mensaje')
    leida = models.BooleanField(default=False, verbose_name='Leída')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} - {self.fecha_creacion.strftime('%d/%m/%Y')}"