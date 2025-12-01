"""
Configuración del panel de administración de Django
"""
from django.contrib import admin
from .models import (
    PerfilUsuario, Proveedor, Evaluacion, PlanMejoramiento,
    DocumentoPlan, AccionMejora, HistorialEstado, PlanAdjunto, Notificacion
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo_perfil', 'activo', 'requiere_cambio_password', 'fecha_creacion']
    list_filter = ['tipo_perfil', 'activo', 'requiere_cambio_password']
    search_fields = ['user__username', 'user__email']
    ordering = ['-fecha_creacion']


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nit', 'razon_social', 'email', 'email_adicional', 'activo']
    list_filter = ['activo', 'fecha_registro']
    search_fields = ['nit', 'razon_social', 'email', 'email_adicional']
    ordering = ['razon_social']


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ['proveedor', 'periodo', 'puntaje', 'fecha', 'requiere_plan']
    list_filter = ['fecha', 'puntaje']
    search_fields = ['proveedor__razon_social', 'proveedor__nit', 'periodo']
    ordering = ['-fecha']
    
    def requiere_plan(self, obj):
        return obj.requiere_plan()
    requiere_plan.boolean = True
    requiere_plan.short_description = 'Requiere Plan'


class DocumentoPlanInline(admin.TabularInline):
    model = DocumentoPlan
    extra = 0


class AccionMejoraInline(admin.TabularInline):
    model = AccionMejora
    extra = 0


class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    readonly_fields = ['fecha_cambio', 'usuario', 'estado_anterior', 'estado_nuevo', 'comentario']


class PlanAdjuntoInline(admin.TabularInline):
    model = PlanAdjunto
    extra = 0
    readonly_fields = ['fecha_subida', 'subido_por']


@admin.register(PlanMejoramiento)
class PlanMejoramientoAdmin(admin.ModelAdmin):
    list_display = ['proveedor', 'get_evaluacion_puntaje', 'estado', 'fecha_envio', 'dias_pendiente']
    list_filter = ['estado', 'fecha_creacion', 'fecha_envio']
    search_fields = ['proveedor__razon_social', 'proveedor__nit']
    readonly_fields = ['fecha_creacion', 'fecha_envio', 'fecha_revision', 'fecha_aprobacion']
    inlines = [AccionMejoraInline, PlanAdjuntoInline, DocumentoPlanInline, HistorialEstadoInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('proveedor', 'evaluacion', 'estado', 'fecha_limite')
        }),
        ('Contenido del Plan', {
            'fields': ('analisis_causa', 'acciones_propuestas', 'responsable',
                      'fecha_implementacion', 'indicadores_seguimiento')
        }),
        ('Revisión', {
            'fields': ('comentarios_tecnico', 'revisado_por', 'fecha_revision')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_envio', 'fecha_aprobacion', 'numero_version'),
            'classes': ('collapse',)
        })
    )
    
    def get_evaluacion_puntaje(self, obj):
        return f"{obj.evaluacion.periodo} - {obj.evaluacion.puntaje}/100"
    get_evaluacion_puntaje.short_description = 'Evaluación'


@admin.register(DocumentoPlan)
class DocumentoPlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'plan', 'fecha_carga']
    list_filter = ['fecha_carga']
    search_fields = ['nombre', 'plan__proveedor__razon_social']


@admin.register(AccionMejora)
class AccionMejoraAdmin(admin.ModelAdmin):
    list_display = ['get_descripcion_corta', 'plan', 'responsable', 'fecha_compromiso', 'completado']
    list_filter = ['completado', 'fecha_compromiso']
    search_fields = ['descripcion', 'plan__proveedor__razon_social']
    
    def get_descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    get_descripcion_corta.short_description = 'Descripción'


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ['plan', 'estado_anterior', 'estado_nuevo', 'fecha_cambio', 'usuario']
    list_filter = ['fecha_cambio', 'estado_nuevo']
    search_fields = ['plan__proveedor__razon_social', 'comentario']
    readonly_fields = ['plan', 'estado_anterior', 'estado_nuevo', 'fecha_cambio', 'usuario', 'comentario']


@admin.register(PlanAdjunto)
class PlanAdjuntoAdmin(admin.ModelAdmin):
    list_display = ['nombre_original', 'tipo_documento', 'plan', 'subido_por', 'fecha_subida']
    list_filter = ['tipo_documento', 'fecha_subida']
    search_fields = ['nombre_original', 'descripcion', 'plan__proveedor__razon_social']
    readonly_fields = ['fecha_subida', 'subido_por']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'plan', 'leida', 'fecha_creacion']
    list_filter = ['tipo', 'leida', 'fecha_creacion']
    search_fields = ['usuario__username', 'mensaje', 'plan__proveedor__razon_social']
    readonly_fields = ['fecha_creacion']
    list_editable = ['leida']