"""
URLs para la aplicación de planes de mejoramiento
"""
from django.urls import path
from . import views
from .views_proveedores import lista_proveedores_nueva, crear_proveedor
from . import views_perfiles
from . import views_estadisticas
from . import views_workflow
from . import views_api

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.redirect_dashboard, name='redirect_dashboard'),
    path('dashboard-redirect/', views_perfiles.dashboard_redirect, name='dashboard_redirect'),
    path('cambiar-password/', views_perfiles.cambiar_password, name='cambiar_password'),

    # ==================== VISTAS DEL GESTOR ====================
    path('gestor/', views_perfiles.dashboard_gestor, name='gestor_dashboard'),
    path('gestor/registros/', views_perfiles.lista_registros_gestor, name='gestor_registros'),
    path('gestor/cargar-evaluacion/', views_perfiles.cargar_evaluacion_automatica, name='gestor_cargar_evaluacion'),
    path('gestor/proveedor/crear/', crear_proveedor, name='gestor_crear_proveedor'),
    path('gestor/estadisticas/', views_estadisticas.dashboard_estadisticas, name='gestor_estadisticas'),
    path('gestor/analytics/', views.dashboard_analytics, name='dashboard_analytics'),

    # ==================== VISTAS DEL GESTOR DE COMPRAS ====================
    path('gestor-compras/', views_perfiles.dashboard_gestor_compras, name='gestor_compras_dashboard'),

    # Gestión de usuarios
    path('gestor/usuarios/', views_perfiles.lista_usuarios, name='gestor_lista_usuarios'),
    path('gestor/usuarios/crear/', views_perfiles.crear_usuario, name='gestor_crear_usuario'),
    path('gestor/usuarios/<int:user_id>/editar/', views_perfiles.editar_usuario, name='gestor_editar_usuario'),
    path('gestor/usuarios/<int:user_id>/eliminar/', views_perfiles.eliminar_usuario, name='gestor_eliminar_usuario'),
    path('gestor/usuarios/<int:user_id>/toggle-estado/', views_perfiles.toggle_estado_usuario, name='gestor_toggle_estado_usuario'),
    path('gestor/proveedores/<int:proveedor_id>/generar-credenciales/', views_perfiles.generar_credenciales_proveedor, name='gestor_generar_credenciales'),

    # ==================== VISTAS DEL TÉCNICO ====================
    path('tecnico/', views_perfiles.dashboard_tecnico, name='tecnico_dashboard'),
    path('tecnico/panel/', views.panel_tecnico, name='tecnico_panel'),
    path('tecnico/proveedores/', lista_proveedores_nueva, name='tecnico_proveedores'),
    path('tecnico/proveedor/crear/', crear_proveedor, name='tecnico_crear_proveedor'),
    path('tecnico/evaluacion/crear/', views.crear_evaluacion, name='tecnico_crear_evaluacion'),
    path('tecnico/evaluacion/crear/<int:proveedor_id>/', views.crear_evaluacion, name='tecnico_crear_evaluacion_proveedor'),
    path('tecnico/revisar/<int:plan_id>/', views_perfiles.revisar_plan, name='tecnico_revisar_plan'),

    # ==================== WORKFLOW Y TRANSICIONES DE ESTADO ====================
    path('plan/<int:plan_id>/cambiar-estado/', views_workflow.cambiar_estado_plan, name='cambiar_estado_plan'),
    path('plan/<int:plan_id>/radicar/', views_workflow.radicar_plan, name='radicar_plan'),
    path('plan/<int:plan_id>/rechazar/', views_workflow.rechazar_plan, name='rechazar_plan'),
    path('plan/<int:plan_id>/solicitar-aclaracion/', views_workflow.solicitar_aclaracion, name='solicitar_aclaracion'),
    path('plan/<int:plan_id>/enviar-carta/', views_workflow.enviar_carta_evaluacion, name='enviar_carta_evaluacion'),
    path('plan/<int:plan_id>/marcar-falta-etica/', views_workflow.marcar_falta_etica, name='marcar_falta_etica'),
    path('plan/<int:plan_id>/historial/', views_workflow.historial_plan, name='historial_plan'),
    path('planes/pendientes-radicacion/', views_workflow.planes_pendientes_radicacion, name='planes_pendientes_radicacion'),
    path('planes/no-recibidos/', views_workflow.planes_no_recibidos, name='planes_no_recibidos'),

    # API/AJAX
    path('api/plan/<int:plan_id>/proximos-estados/', views_workflow.obtener_proximos_estados_ajax, name='obtener_proximos_estados_ajax'),
    path('api/tipos-calificacion/', views_api.obtener_tipos_calificacion, name='api_tipos_calificacion'),
    path('api/criterios-tipo/<int:tipo_id>/', views_api.obtener_criterios_por_tipo, name='api_criterios_por_tipo'),

    # ==================== MANUAL DE USUARIO ====================
    path('manual/', views.manual_usuario, name='manual_usuario'),

    # ==================== VISTAS DEL PROVEEDOR ====================
    path('proveedor/', views.dashboard_proveedor, name='proveedor_dashboard'),
    path('proveedor/evaluacion/<int:evaluacion_id>/', views.ver_evaluacion, name='proveedor_ver_evaluacion'),
    path('proveedor/plan/crear/', views.crear_plan, name='proveedor_crear_plan'),
    path('proveedor/plan/<int:plan_id>/', views.ver_plan, name='proveedor_ver_plan'),
    path('proveedor/plan/<int:plan_id>/editar/', views.editar_plan, name='proveedor_editar_plan'),

    # ==================== COMPATIBILIDAD (legacy) ====================
    path('dashboard/', views.dashboard_proveedor, name='dashboard_proveedor'),
    path('evaluacion/<int:evaluacion_id>/', views.ver_evaluacion, name='ver_evaluacion'),
    path('plan/crear/', views.crear_plan, name='crear_plan'),
    path('plan/<int:plan_id>/', views.ver_plan, name='ver_plan'),
    path('plan/<int:plan_id>/editar/', views.editar_plan, name='editar_plan'),
    path('dashboard_gestor/', views_perfiles.dashboard_gestor, name='dashboard_gestor'),
    path('lista_registros_gestor/', views_perfiles.lista_registros_gestor, name='lista_registros_gestor'),
    path('cargar_evaluacion/', views_perfiles.cargar_evaluacion_automatica, name='cargar_evaluacion'),
    path('crear_proveedor_gestor/', crear_proveedor, name='crear_proveedor_gestor'),
    path('dashboard_estadisticas/', views_estadisticas.dashboard_estadisticas, name='dashboard_estadisticas'),
    path('panel_tecnico/', views.panel_tecnico, name='panel_tecnico'),
    path('lista_proveedores/', lista_proveedores_nueva, name='lista_proveedores'),
    path('crear_proveedor/', crear_proveedor, name='crear_proveedor'),
    path('crear_evaluacion/', views.crear_evaluacion, name='crear_evaluacion'),
    path('crear_evaluacion_proveedor/<int:proveedor_id>/', views.crear_evaluacion, name='crear_evaluacion_proveedor'),
    path('revisar_plan_tecnico/<int:plan_id>/', views_perfiles.revisar_plan, name='revisar_plan_tecnico'),
]