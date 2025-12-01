"""
Script para crear datos de prueba en el sistema de planes de mejoramiento
Ejecutar con: python manage.py shell < crear_datos_prueba.py
"""

from django.contrib.auth.models import User
from planes.models import Proveedor, Evaluacion, PlanMejoramiento, AccionMejora, HistorialEstado
from datetime import date, timedelta
from django.utils import timezone
import random

print("=" * 50)
print("CREANDO DATOS DE PRUEBA")
print("=" * 50)

# Limpiar datos existentes (opcional - comentar en producción)
print("\n1. Limpiando datos existentes...")
User.objects.filter(username__startswith='9').delete()
User.objects.filter(username='tecnico1').delete()
User.objects.filter(username='tecnico2').delete()
print("   - Datos limpiados")

# Crear usuarios técnicos
print("\n2. Creando usuarios técnicos...")
tecnico1 = User.objects.create_user(
    username='tecnico1',
    password='admin123',
    first_name='Carlos',
    last_name='Mendoza',
    email='carlos.mendoza@intercolombia.com'
)
print(f"   ✓ Técnico creado: {tecnico1.username} / admin123")

tecnico2 = User.objects.create_user(
    username='tecnico2',
    password='admin123',
    first_name='María',
    last_name='González',
    email='maria.gonzalez@intercolombia.com'
)
print(f"   ✓ Técnico creado: {tecnico2.username} / admin123")

# Crear superusuario
print("\n3. Creando superusuario...")
try:
    admin = User.objects.create_superuser(
        username='admin',
        password='admin123',
        email='admin@intercolombia.com'
    )
    print(f"   ✓ Superusuario creado: admin / admin123")
except:
    print("   - Superusuario ya existe")

# Datos de proveedores de ejemplo
proveedores_data = [
    {
        'nit': '900123456',
        'razon_social': 'Suministros Industriales ABC S.A.S.',
        'email': 'contacto@suministrosabc.com',
        'telefono': '3001234567',
        'puntaje': 72,  # Requiere plan
        'desglose': {'calidad': 85, 'entrega': 45, 'documentacion': 70, 'precio': 90}
    },
    {
        'nit': '900234567',
        'razon_social': 'Logística y Transportes XYZ Ltda.',
        'email': 'info@logisticaxyz.com',
        'telefono': '3112345678',
        'puntaje': 65,  # Requiere plan
        'desglose': {'calidad': 70, 'entrega': 50, 'documentacion': 65, 'precio': 75}
    },
    {
        'nit': '900345678',
        'razon_social': 'Servicios Técnicos 123 S.A.',
        'email': 'servicios@tecnicos123.com',
        'telefono': '3223456789',
        'puntaje': 75,  # Requiere plan
        'desglose': {'calidad': 80, 'entrega': 70, 'documentacion': 70, 'precio': 80}
    },
    {
        'nit': '900456789',
        'razon_social': 'Comercializadora DEF Colombia',
        'email': 'ventas@defcolombia.com',
        'telefono': '3334567890',
        'puntaje': 85,  # No requiere plan
        'desglose': {'calidad': 90, 'entrega': 85, 'documentacion': 80, 'precio': 85}
    },
    {
        'nit': '900567890',
        'razon_social': 'Ingeniería y Consultoría GHI',
        'email': 'proyectos@ingenieroghi.com',
        'telefono': '3445678901',
        'puntaje': 55,  # Requiere plan urgente
        'desglose': {'calidad': 60, 'entrega': 40, 'documentacion': 55, 'precio': 65}
    }
]

print("\n4. Creando proveedores y evaluaciones...")
for i, data in enumerate(proveedores_data, 1):
    # Crear usuario para el proveedor
    user = User.objects.create_user(
        username=data['nit'],
        password='proveedor123',
        email=data['email']
    )
    
    # Crear proveedor
    proveedor = Proveedor.objects.create(
        user=user,
        nit=f"{data['nit'][:3]}.{data['nit'][3:6]}.{data['nit'][6:]}-7",
        razon_social=data['razon_social'],
        email=data['email'],
        telefono=data['telefono']
    )
    
    # Crear evaluación actual (Q1 2024)
    evaluacion_actual = Evaluacion.objects.create(
        proveedor=proveedor,
        periodo='2024-Q1',
        puntaje=data['puntaje'],
        fecha=date.today() - timedelta(days=30),
        puntaje_calidad=data['desglose']['calidad'],
        puntaje_entrega=data['desglose']['entrega'],
        puntaje_documentacion=data['desglose']['documentacion'],
        puntaje_precio=data['desglose']['precio'],
        observaciones=f"Evaluación del primer trimestre 2024. {'Requiere plan de mejoramiento.' if data['puntaje'] < 80 else 'Desempeño satisfactorio.'}"
    )
    
    # Crear evaluaciones históricas
    for q in range(1, 4):
        periodo = f"2023-Q{5-q}"
        puntaje_historico = data['puntaje'] + random.randint(-10, 15)
        puntaje_historico = max(50, min(100, puntaje_historico))  # Mantener entre 50 y 100
        
        Evaluacion.objects.create(
            proveedor=proveedor,
            periodo=periodo,
            puntaje=puntaje_historico,
            fecha=date.today() - timedelta(days=90*q + 30),
            puntaje_calidad=random.randint(60, 95),
            puntaje_entrega=random.randint(60, 95),
            puntaje_documentacion=random.randint(60, 95),
            puntaje_precio=random.randint(60, 95),
            observaciones=f"Evaluación histórica del período {periodo}"
        )
    
    print(f"   ✓ Proveedor {i}: {data['razon_social']} - NIT: {data['nit']} - Puntaje: {data['puntaje']}/100")
    
    # Crear plan de mejoramiento si requiere
    if data['puntaje'] < 80:
        # Decidir el estado del plan
        if i == 1:  # Primer proveedor: plan enviado
            estado = 'ENVIADO'
            comentarios = ''
        elif i == 2:  # Segundo proveedor: en revisión
            estado = 'EN_REVISION'
            comentarios = ''
        elif i == 3:  # Tercer proveedor: requiere ajustes
            estado = 'REQUIERE_AJUSTES'
            comentarios = 'El plan necesita más detalle en los indicadores de medición. Por favor, especifique cómo medirá la reducción de tiempos de entrega.'
        else:  # Quinto proveedor: plan aprobado
            estado = 'APROBADO'
            comentarios = 'Plan aprobado. Se realizará seguimiento trimestral.'
        
        plan = PlanMejoramiento.objects.create(
            evaluacion=evaluacion_actual,
            proveedor=proveedor,
            estado=estado,
            analisis_causa=f"""
            Después de analizar los resultados de la evaluación, hemos identificado las siguientes causas raíz:
            1. Falta de procedimientos estandarizados en el área de {['calidad', 'entrega', 'documentación'][i % 3]}
            2. Capacitación insuficiente del personal operativo
            3. Sistemas de control y seguimiento inadecuados
            4. Comunicación deficiente con los stakeholders
            """,
            acciones_propuestas=f"""
            Para abordar las causas identificadas, proponemos:
            - Implementar un sistema de gestión de calidad ISO 9001
            - Capacitar al 100% del personal en los próximos 3 meses
            - Establecer KPIs y dashboards de seguimiento
            - Crear canales de comunicación directa con Intercolombia
            """,
            responsable=f"Gerente de {'Calidad' if i == 1 else 'Operaciones' if i == 2 else 'Logística'}",
            fecha_implementacion=date.today() + timedelta(days=90),
            indicadores_seguimiento="""
            - Reducción del 30% en tiempos de respuesta
            - Aumento del 25% en satisfacción del cliente
            - Cero no conformidades críticas
            - 95% de entregas a tiempo
            """,
            fecha_envio=timezone.now() - timedelta(days=random.randint(1, 15)),
            comentarios_tecnico=comentarios if comentarios else '',
            revisado_por=tecnico1 if estado in ['REQUIERE_AJUSTES', 'APROBADO'] else None,
            fecha_revision=timezone.now() if estado in ['REQUIERE_AJUSTES', 'APROBADO'] else None,
            fecha_aprobacion=timezone.now() if estado == 'APROBADO' else None
        )
        
        # Crear acciones de mejora específicas
        acciones = [
            {
                'descripcion': 'Implementar sistema de tracking GPS para todos los envíos',
                'responsable': 'Jefe de Logística',
                'fecha': date.today() + timedelta(days=30),
                'indicador': 'l00% de envíos con tracking activo'
            },
            {
                'descripcion': 'Capacitar al personal en gestión de calidad',
                'responsable': 'Recursos Humanos',
                'fecha': date.today() + timedelta(days=45),
                'indicador': '100% del personal capacitado'
            },
            {
                'descripcion': 'Establecer stock de seguridad mínimo de 15 días',
                'responsable': 'Jefe de Almacén',
                'fecha': date.today() + timedelta(days=60),
                'indicador': 'Nivel de stock >= 15 días continuos'
            }
        ]
        
        for accion_data in acciones:
            AccionMejora.objects.create(
                plan=plan,
                descripcion=accion_data['descripcion'],
                responsable=accion_data['responsable'],
                fecha_compromiso=accion_data['fecha'],
                indicador=accion_data['indicador']
            )
        
        # Crear historial de estados
        HistorialEstado.objects.create(
            plan=plan,
            estado_anterior='BORRADOR',
            estado_nuevo='ENVIADO',
            usuario=user,
            comentario='Plan creado y enviado para revisión',
            fecha_cambio=plan.fecha_envio
        )
        
        if estado in ['EN_REVISION', 'REQUIERE_AJUSTES', 'APROBADO']:
            HistorialEstado.objects.create(
                plan=plan,
                estado_anterior='ENVIADO',
                estado_nuevo='EN_REVISION',
                usuario=tecnico1,
                comentario='Plan en proceso de revisión',
                fecha_cambio=plan.fecha_envio + timedelta(hours=4)
            )
        
        if estado in ['REQUIERE_AJUSTES', 'APROBADO']:
            HistorialEstado.objects.create(
                plan=plan,
                estado_anterior='EN_REVISION',
                estado_nuevo=estado,
                usuario=tecnico1,
                comentario=comentarios if comentarios else 'Plan aprobado satisfactoriamente',
                fecha_cambio=timezone.now()
            )
        
        print(f"      → Plan de mejoramiento creado - Estado: {estado}")

print("\n" + "=" * 50)
print("RESUMEN DE DATOS CREADOS")
print("=" * 50)
print(f"\n✓ Técnicos: 2")
print(f"✓ Proveedores: {len(proveedores_data)}")
print(f"✓ Evaluaciones: {Evaluacion.objects.count()}")
print(f"✓ Planes de mejoramiento: {PlanMejoramiento.objects.count()}")
print(f"✓ Acciones de mejora: {AccionMejora.objects.count()}")

print("\n" + "=" * 50)
print("CREDENCIALES DE ACCESO")
print("=" * 50)
print("\nSUPERUSUARIO:")
print("  Usuario: admin")
print("  Contraseña: admin123")
print("\nTÉCNICOS:")
print("  Usuario: tecnico1 | Contraseña: admin123")
print("  Usuario: tecnico2 | Contraseña: admin123")
print("\nPROVEEDORES:")
for data in proveedores_data:
    print(f"  {data['razon_social'][:30]:30} | Usuario: {data['nit']} | Contraseña: proveedor123")

print("\n" + "=" * 50)
print("¡DATOS DE PRUEBA CREADOS EXITOSAMENTE!")
print("=" * 50)
print("\nPuede iniciar el servidor con: python manage.py runserver")
print("Acceder en: http://localhost:8000/")
print("Panel de administración: http://localhost:8000/admin/")