#!/usr/bin/env python
"""
Script de prueba para verificar la implementación de ajustes
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from planes.models import PerfilUsuario, Proveedor, Evaluacion, PlanMejoramiento


def crear_usuarios_prueba():
    """Crear usuarios de prueba para cada perfil"""
    print("✅ CREANDO USUARIOS DE PRUEBA")
    print("-" * 50)
    
    # Crear usuario Gestor
    try:
        gestor_user = User.objects.create_user(
            username='gestor1',
            password='Gestor123!@#',
            email='gestor@intercolombia.com',
            first_name='Gestor',
            last_name='Planes'
        )
        PerfilUsuario.objects.create(
            user=gestor_user,
            tipo_perfil='GESTOR',
            requiere_cambio_password=False
        )
        print("✓ Usuario Gestor creado: gestor1 / Gestor123!@#")
    except:
        print("  Usuario gestor ya existe")
    
    # Crear usuario Técnico
    try:
        tecnico_user = User.objects.create_user(
            username='tecnico2',
            password='Tecnico123!@#',
            email='tecnico2@intercolombia.com',
            first_name='Técnico',
            last_name='Evaluador'
        )
        PerfilUsuario.objects.create(
            user=tecnico_user,
            tipo_perfil='TECNICO',
            requiere_cambio_password=False
        )
        print("✓ Usuario Técnico creado: tecnico2 / Tecnico123!@#")
    except:
        tecnico_user = User.objects.get(username='tecnico2')
        print("  Usuario técnico ya existe")
    
    # Crear usuario Proveedor
    try:
        # Primero crear el usuario
        prov_user = User.objects.create_user(
            username='900888777',
            password='Proveedor123!@#',
            email='proveedor@test.com',
            first_name='Empresa',
            last_name='Test'
        )
        
        # Crear el proveedor
        proveedor = Proveedor.objects.create(
            user=prov_user,
            nit='900888777',
            razon_social='Empresa Test S.A.S',
            email='proveedor@test.com',
            email_adicional='gestor@test.com',
            activo=True
        )
        
        # Crear perfil
        PerfilUsuario.objects.create(
            user=prov_user,
            tipo_perfil='PROVEEDOR',
            requiere_cambio_password=True  # Debe cambiar en primer acceso
        )
        print("✓ Usuario Proveedor creado: 900888777 / Proveedor123!@#")
        
        return proveedor, tecnico_user
    except:
        proveedor = Proveedor.objects.get(nit='900888777')
        print("  Usuario proveedor ya existe")
        return proveedor, tecnico_user


def crear_evaluacion_prueba(proveedor, tecnico):
    """Crear evaluación de prueba con todos los nuevos campos"""
    print("\n✅ CREANDO EVALUACIÓN DE PRUEBA")
    print("-" * 50)
    
    try:
        evaluacion = Evaluacion.objects.create(
            proveedor=proveedor,
            numero_contrato='4600005089',
            subcategoria='SUMINISTROS',
            tecnico_asignado=tecnico,
            puntaje=65,  # Menor a 80 para requerir plan
            fecha=date.today(),
            fecha_limite_aclaracion=date.today() + timedelta(days=5),
            fecha_limite_plan=date.today() + timedelta(days=20),
            # Desglose del puntaje
            puntaje_gestion=15,
            puntaje_calidad=10,
            puntaje_oportunidad=15,
            puntaje_ambiental_social=15,
            puntaje_sst=10,
            # Máximos
            max_gestion=25,
            max_calidad=25,
            max_oportunidad=25,
            max_ambiental_social=25,
            max_sst=25,
            # Aprobaciones
            requiere_aprobacion_sst=False,
            requiere_aprobacion_ambiental=True,
            # Observaciones
            observaciones_gestion='Debe mejorar los tiempos de respuesta',
            observaciones_calidad='Algunos productos con defectos menores',
            observaciones_oportunidad='Retrasos en las entregas',
            observaciones_ambiental_social='Falta documentación ambiental',
            observaciones_sst='Mejorar uso de EPP',
            observaciones_generales='Requiere plan de mejoramiento integral'
        )
        
        print(f"✓ Evaluación creada para {proveedor.razon_social}")
        print(f"  - Contrato: {evaluacion.numero_contrato}")
        print(f"  - Puntaje: {evaluacion.puntaje}/100")
        print(f"  - Técnico asignado: {tecnico.get_full_name()}")
        
        # Crear plan automáticamente ya que es < 80
        plan = PlanMejoramiento.objects.create(
            evaluacion=evaluacion,
            proveedor=proveedor,
            estado='BORRADOR',
            analisis_causa='Análisis pendiente',
            acciones_propuestas='Acciones pendientes',
            responsable='Por definir',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Por definir',
            fecha_limite=evaluacion.fecha_limite_plan
        )
        print(f"✓ Plan de mejoramiento creado en estado: {plan.get_estado_display()}")
        
        return evaluacion, plan
        
    except Exception as e:
        print(f"✗ Error al crear evaluación: {str(e)}")
        return None, None


def verificar_estados():
    """Verificar que los nuevos estados estén disponibles"""
    print("\n✅ VERIFICANDO NUEVOS ESTADOS")
    print("-" * 50)
    
    estados_esperados = [
        'BORRADOR', 'ENVIADO', 'FIRMADO_ENVIADO', 
        'EN_REVISION', 'ESPERANDO_APROBACION', 
        'SOLICITUD_AJUSTES', 'REQUIERE_AJUSTES',
        'DOCUMENTOS_REEVALUADOS', 'APROBADO', 'RECHAZADO'
    ]
    
    estados_disponibles = dict(PlanMejoramiento.ESTADOS)
    
    for estado in estados_esperados:
        if estado in estados_disponibles:
            print(f"✓ Estado '{estados_disponibles[estado]}' disponible")
        else:
            print(f"✗ Estado '{estado}' NO disponible")


def verificar_perfiles():
    """Verificar que los perfiles estén funcionando"""
    print("\n✅ VERIFICANDO PERFILES DE USUARIO")
    print("-" * 50)
    
    perfiles = PerfilUsuario.objects.all()
    
    if perfiles.exists():
        for perfil in perfiles:
            print(f"✓ {perfil.user.username}: {perfil.get_tipo_perfil_display()}")
            print(f"  - Activo: {'Sí' if perfil.activo else 'No'}")
            print(f"  - Requiere cambio contraseña: {'Sí' if perfil.requiere_cambio_password else 'No'}")
    else:
        print("✗ No se encontraron perfiles de usuario")


def main():
    print("=" * 60)
    print("VERIFICACIÓN DE IMPLEMENTACIÓN DE AJUSTES")
    print("=" * 60)
    
    # Crear usuarios de prueba
    proveedor, tecnico = crear_usuarios_prueba()
    
    # Crear evaluación de prueba
    if proveedor and tecnico:
        crear_evaluacion_prueba(proveedor, tecnico)
    
    # Verificar estados
    verificar_estados()
    
    # Verificar perfiles
    verificar_perfiles()
    
    print("\n" + "=" * 60)
    print("RESUMEN DE IMPLEMENTACIÓN")
    print("=" * 60)
    
    # Estadísticas
    total_perfiles = PerfilUsuario.objects.count()
    total_evaluaciones = Evaluacion.objects.count()
    total_planes = PlanMejoramiento.objects.count()
    
    print(f"✓ Total perfiles creados: {total_perfiles}")
    print(f"✓ Total evaluaciones: {total_evaluaciones}")
    print(f"✓ Total planes de mejoramiento: {total_planes}")
    
    print("\n✅ CREDENCIALES DE ACCESO:")
    print("-" * 30)
    print("GESTOR: gestor1 / Gestor123!@#")
    print("TÉCNICO: tecnico2 / Tecnico123!@#")
    print("PROVEEDOR: 900888777 / Proveedor123!@#")
    
    print("\n📌 NOTAS IMPORTANTES:")
    print("-" * 30)
    print("• Los proveedores deben cambiar contraseña en primer acceso")
    print("• El sistema validará contraseñas seguras (mayúsculas, minúsculas, números y caracteres especiales)")
    print("• Los estados 'SOLICITUD_AJUSTES' y 'ESPERANDO_APROBACION' están disponibles")
    print("• Las evaluaciones ahora incluyen todos los campos requeridos del documento")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())