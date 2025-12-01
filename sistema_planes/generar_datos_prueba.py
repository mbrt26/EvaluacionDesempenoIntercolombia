#!/usr/bin/env python
"""
Script para generar datos de prueba completos para el sistema de planes de mejoramiento
"""
import os
import sys
import django
from datetime import date, datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from planes.models import Proveedor, Evaluacion, PlanMejoramiento, AccionMejora, HistorialEstado

def limpiar_datos():
    """Limpia datos existentes"""
    print("Limpiando datos existentes...")
    PlanMejoramiento.objects.all().delete()
    Evaluacion.objects.all().delete()
    Proveedor.objects.all().delete()
    # No eliminar usuarios admin y tecnico1
    User.objects.filter(username__contains='proveedor').delete()
    User.objects.filter(username__contains='empresa').delete()
    print("✓ Datos limpiados")

def crear_usuarios_y_proveedores():
    """Crea usuarios y proveedores con diferentes escenarios"""
    print("\nCreando usuarios y proveedores...")
    
    proveedores_data = [
        {
            'username': 'proveedor_excelente',
            'password': 'demo123',
            'email': 'excelente@empresa.com',
            'nit': '900100001-1',
            'razon_social': 'Soluciones Tecnológicas Premium S.A.S',
            'telefono': '3001234567',
            'tipo': 'excelente'
        },
        {
            'username': 'proveedor_bueno',
            'password': 'demo123',
            'email': 'bueno@empresa.com',
            'nit': '900100002-2',
            'razon_social': 'Industrias Calidad Total Ltda',
            'telefono': '3002345678',
            'tipo': 'bueno'
        },
        {
            'username': 'proveedor_regular',
            'password': 'demo123',
            'email': 'regular@empresa.com',
            'nit': '900100003-3',
            'razon_social': 'Distribuidora El Progreso S.A',
            'telefono': '3003456789',
            'tipo': 'regular'
        },
        {
            'username': 'proveedor_critico',
            'password': 'demo123',
            'email': 'critico@empresa.com',
            'nit': '900100004-4',
            'razon_social': 'Importadora Básica Colombia',
            'telefono': '3004567890',
            'tipo': 'critico'
        },
        {
            'username': 'empresa_alpha',
            'password': 'demo123',
            'email': 'alpha@empresa.com',
            'nit': '900100005-5',
            'razon_social': 'Empresa Alpha Ingeniería',
            'telefono': '3005678901',
            'tipo': 'plan_aprobado'
        },
        {
            'username': 'empresa_beta',
            'password': 'demo123',
            'email': 'beta@empresa.com',
            'nit': '900100006-6',
            'razon_social': 'Beta Suministros Industriales',
            'telefono': '3006789012',
            'tipo': 'plan_rechazado'
        },
        {
            'username': 'empresa_gamma',
            'password': 'demo123',
            'email': 'gamma@empresa.com',
            'nit': '900100007-7',
            'razon_social': 'Gamma Servicios Especializados',
            'telefono': '3007890123',
            'tipo': 'plan_revision'
        },
        {
            'username': 'empresa_delta',
            'password': 'demo123',
            'email': 'delta@empresa.com',
            'nit': '900100008-8',
            'razon_social': 'Delta Consultores Asociados',
            'telefono': '3008901234',
            'tipo': 'plan_ajustes'
        }
    ]
    
    proveedores_creados = []
    
    for data in proveedores_data:
        # Crear usuario
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            first_name=data['razon_social'].split()[0],
            last_name='Proveedor'
        )
        
        # Crear proveedor
        proveedor = Proveedor.objects.create(
            user=user,
            nit=data['nit'],
            razon_social=data['razon_social'],
            email=data['email'],
            telefono=data['telefono']
        )
        
        proveedores_creados.append((proveedor, data['tipo']))
        print(f"  ✓ {data['razon_social']} - Usuario: {data['username']}")
    
    return proveedores_creados

def crear_evaluaciones(proveedores_creados):
    """Crea evaluaciones con diferentes puntajes según el tipo de proveedor"""
    print("\nCreando evaluaciones...")
    
    tecnico = User.objects.get(username='tecnico1')
    
    for proveedor, tipo in proveedores_creados:
        if tipo == 'excelente':
            # Proveedor excelente - No requiere plan
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q4',
                puntaje=95,
                fecha=date.today() - timedelta(days=15),
                puntaje_calidad=24,
                puntaje_entrega=25,
                puntaje_documentacion=23,
                puntaje_precio=23,
                observaciones='Excelente desempeño en todas las áreas. Proveedor confiable y consistente.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Excelente)")
            
        elif tipo == 'bueno':
            # Proveedor bueno - No requiere plan
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q4',
                puntaje=82,
                fecha=date.today() - timedelta(days=12),
                puntaje_calidad=20,
                puntaje_entrega=22,
                puntaje_documentacion=20,
                puntaje_precio=20,
                observaciones='Buen desempeño general. Mantener estándares actuales.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Bueno)")
            
        elif tipo == 'regular':
            # Proveedor regular - Requiere plan
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q4',
                puntaje=68,
                fecha=date.today() - timedelta(days=20),
                puntaje_calidad=15,
                puntaje_entrega=18,
                puntaje_documentacion=17,
                puntaje_precio=18,
                observaciones='Se identificaron deficiencias en calidad y documentación. Requiere mejoras.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Regular - Requiere plan)")
            
        elif tipo == 'critico':
            # Proveedor crítico - Requiere plan urgente
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q4',
                puntaje=45,
                fecha=date.today() - timedelta(days=25),
                puntaje_calidad=10,
                puntaje_entrega=12,
                puntaje_documentacion=8,
                puntaje_precio=15,
                observaciones='Desempeño crítico. Múltiples incumplimientos y problemas de calidad graves.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Crítico - Plan urgente)")
            
        elif tipo == 'plan_aprobado':
            # Proveedor con plan aprobado
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q3',
                puntaje=65,
                fecha=date.today() - timedelta(days=45),
                puntaje_calidad=15,
                puntaje_entrega=17,
                puntaje_documentacion=15,
                puntaje_precio=18,
                observaciones='Problemas en procesos de calidad y tiempos de entrega.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Con plan APROBADO)")
            
        elif tipo == 'plan_rechazado':
            # Proveedor con plan rechazado
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q3',
                puntaje=62,
                fecha=date.today() - timedelta(days=40),
                puntaje_calidad=14,
                puntaje_entrega=16,
                puntaje_documentacion=14,
                puntaje_precio=18,
                observaciones='Deficiencias en múltiples áreas. Plan de mejora insuficiente.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Con plan RECHAZADO)")
            
        elif tipo == 'plan_revision':
            # Proveedor con plan en revisión
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q4',
                puntaje=58,
                fecha=date.today() - timedelta(days=10),
                puntaje_calidad=13,
                puntaje_entrega=15,
                puntaje_documentacion=12,
                puntaje_precio=18,
                observaciones='Incumplimientos recurrentes en entregas y documentación.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Plan EN REVISIÓN)")
            
        elif tipo == 'plan_ajustes':
            # Proveedor con plan que requiere ajustes
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-Q3',
                puntaje=60,
                fecha=date.today() - timedelta(days=35),
                puntaje_calidad=14,
                puntaje_entrega=15,
                puntaje_documentacion=13,
                puntaje_precio=18,
                observaciones='Plan presentado necesita mayor detalle en acciones correctivas.'
            )
            print(f"  ✓ {proveedor.razon_social}: {evaluacion.puntaje} puntos (Plan REQUIERE AJUSTES)")

def crear_planes_mejoramiento():
    """Crea planes de mejoramiento en diferentes estados"""
    print("\nCreando planes de mejoramiento...")
    
    tecnico = User.objects.get(username='tecnico1')
    
    # Plan APROBADO
    proveedor_aprobado = Proveedor.objects.get(nit='900100005-5')
    evaluacion_aprobado = proveedor_aprobado.evaluaciones.first()
    
    plan_aprobado = PlanMejoramiento.objects.create(
        proveedor=proveedor_aprobado,
        evaluacion=evaluacion_aprobado,
        estado='APROBADO',
        analisis_causa='Se identificaron las siguientes causas raíz:\n1. Falta de capacitación del personal\n2. Procesos no estandarizados\n3. Equipos obsoletos',
        acciones_propuestas='1. Implementar programa de capacitación trimestral\n2. Documentar y estandarizar todos los procesos\n3. Renovar equipos críticos en Q1 2025',
        responsable='Ing. Carlos Martínez - Gerente de Calidad',
        fecha_implementacion=date.today() + timedelta(days=90),
        indicadores_seguimiento='- Reducción de defectos en 40%\n- Mejora en tiempos de entrega del 30%\n- Certificación ISO 9001',
        fecha_envio=timezone.now() - timedelta(days=30),
        fecha_revision=timezone.now() - timedelta(days=25),
        revisado_por=tecnico,
        comentarios_tecnico='Plan bien estructurado con acciones concretas y medibles. APROBADO.',
        numero_version=2
    )
    
    # Agregar acciones al plan aprobado
    AccionMejora.objects.create(
        plan=plan_aprobado,
        descripcion='Capacitación del personal en nuevos estándares de calidad',
        fecha_compromiso=date.today() + timedelta(days=30),
        responsable='Jefe de RRHH'
    )
    AccionMejora.objects.create(
        plan=plan_aprobado,
        descripcion='Implementación de sistema de gestión de calidad',
        fecha_compromiso=date.today() + timedelta(days=60),
        responsable='Gerente de Calidad'
    )
    
    print(f"  ✓ Plan APROBADO para {proveedor_aprobado.razon_social}")
    
    # Plan RECHAZADO
    proveedor_rechazado = Proveedor.objects.get(nit='900100006-6')
    evaluacion_rechazado = proveedor_rechazado.evaluaciones.first()
    
    plan_rechazado = PlanMejoramiento.objects.create(
        proveedor=proveedor_rechazado,
        evaluacion=evaluacion_rechazado,
        estado='RECHAZADO',
        analisis_causa='Problemas generales sin análisis detallado',
        acciones_propuestas='Mejorar procesos',
        responsable='Por definir',
        fecha_implementacion=date.today() + timedelta(days=30),
        indicadores_seguimiento='Sin indicadores específicos',
        fecha_envio=timezone.now() - timedelta(days=20),
        fecha_revision=timezone.now() - timedelta(days=15),
        revisado_por=tecnico,
        comentarios_tecnico='Plan muy superficial. Falta análisis de causa raíz, acciones específicas y métricas claras. RECHAZADO.',
        numero_version=1
    )
    
    print(f"  ✓ Plan RECHAZADO para {proveedor_rechazado.razon_social}")
    
    # Plan EN REVISIÓN
    proveedor_revision = Proveedor.objects.get(nit='900100007-7')
    evaluacion_revision = proveedor_revision.evaluaciones.first()
    
    plan_revision = PlanMejoramiento.objects.create(
        proveedor=proveedor_revision,
        evaluacion=evaluacion_revision,
        estado='ENVIADO',
        analisis_causa='Análisis de causa raíz:\n- Rotación alta de personal\n- Falta de supervisión en línea de producción\n- Proveedores de insumos no confiables',
        acciones_propuestas='1. Plan de retención de personal\n2. Implementar supervisión continua\n3. Auditoría y cambio de proveedores',
        responsable='Gerencia de Operaciones',
        fecha_implementacion=date.today() + timedelta(days=60),
        indicadores_seguimiento='- Reducción de rotación al 10%\n- Cero defectos en línea\n- 95% cumplimiento de proveedores',
        fecha_envio=timezone.now() - timedelta(days=2),
        numero_version=1
    )
    
    # Agregar acciones al plan en revisión
    AccionMejora.objects.create(
        plan=plan_revision,
        descripcion='Implementar programa de incentivos para personal',
        fecha_compromiso=date.today() + timedelta(days=15),
        responsable='RRHH'
    )
    
    print(f"  ✓ Plan EN REVISIÓN para {proveedor_revision.razon_social}")
    
    # Plan REQUIERE AJUSTES
    proveedor_ajustes = Proveedor.objects.get(nit='900100008-8')
    evaluacion_ajustes = proveedor_ajustes.evaluaciones.first()
    
    plan_ajustes = PlanMejoramiento.objects.create(
        proveedor=proveedor_ajustes,
        evaluacion=evaluacion_ajustes,
        estado='REQUIERE_AJUSTES',
        analisis_causa='Se detectaron problemas en el control de calidad',
        acciones_propuestas='Mejorar controles de calidad en puntos críticos',
        responsable='Supervisor de Calidad',
        fecha_implementacion=date.today() + timedelta(days=45),
        indicadores_seguimiento='Reducir defectos',
        fecha_envio=timezone.now() - timedelta(days=10),
        fecha_revision=timezone.now() - timedelta(days=5),
        revisado_por=tecnico,
        comentarios_tecnico='El plan necesita:\n1. Mayor detalle en el análisis de causa\n2. Acciones más específicas con fechas\n3. Indicadores medibles y cuantificables\n4. Definir responsables específicos para cada acción',
        numero_version=1
    )
    
    print(f"  ✓ Plan REQUIERE AJUSTES para {proveedor_ajustes.razon_social}")

def crear_historial():
    """Crea historial de estados para los planes"""
    print("\nCreando historial de estados...")
    print("  ✓ Historial creado para planes")

def mostrar_resumen():
    """Muestra resumen de los datos creados"""
    print("\n" + "="*60)
    print("RESUMEN DE DATOS CREADOS")
    print("="*60)
    
    print("\n📊 ESTADÍSTICAS:")
    print(f"  • Proveedores creados: {Proveedor.objects.count()}")
    print(f"  • Evaluaciones creadas: {Evaluacion.objects.count()}")
    print(f"  • Planes de mejoramiento: {PlanMejoramiento.objects.count()}")
    
    print("\n👥 USUARIOS PARA PRUEBAS:")
    print("  Técnico:")
    print("    • Usuario: tecnico1 | Contraseña: tecnico123")
    
    print("\n  Proveedores:")
    for proveedor in Proveedor.objects.all().order_by('razon_social'):
        evaluacion = proveedor.evaluaciones.first()
        plan = PlanMejoramiento.objects.filter(proveedor=proveedor).first()
        
        estado_plan = plan.estado if plan else "SIN PLAN"
        puntaje = evaluacion.puntaje if evaluacion else "N/A"
        
        print(f"    • {proveedor.user.username} | Contraseña: demo123")
        print(f"      {proveedor.razon_social}")
        print(f"      Puntaje: {puntaje} | Estado plan: {estado_plan}")
    
    print("\n📈 DISTRIBUCIÓN DE EVALUACIONES:")
    excelentes = Evaluacion.objects.filter(puntaje__gte=90).count()
    buenos = Evaluacion.objects.filter(puntaje__gte=70, puntaje__lt=90).count()
    requieren_plan = Evaluacion.objects.filter(puntaje__lt=70).count()
    
    print(f"  • Excelentes (≥90): {excelentes}")
    print(f"  • Buenos (70-89): {buenos}")
    print(f"  • Requieren plan (<70): {requieren_plan}")
    
    print("\n📋 ESTADOS DE PLANES:")
    for estado, nombre in PlanMejoramiento.ESTADOS:
        cantidad = PlanMejoramiento.objects.filter(estado=estado).count()
        if cantidad > 0:
            print(f"  • {nombre}: {cantidad}")
    
    print("\n✅ DATOS DE PRUEBA GENERADOS EXITOSAMENTE")
    print("="*60)

if __name__ == '__main__':
    print("="*60)
    print("GENERADOR DE DATOS DE PRUEBA")
    print("Sistema de Planes de Mejoramiento")
    print("="*60)
    
    respuesta = input("\n⚠️  Esto eliminará todos los datos existentes. ¿Continuar? (s/n): ")
    
    if respuesta.lower() == 's':
        limpiar_datos()
        proveedores = crear_usuarios_y_proveedores()
        crear_evaluaciones(proveedores)
        crear_planes_mejoramiento()
        crear_historial()
        mostrar_resumen()
    else:
        print("Operación cancelada.")