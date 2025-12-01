#!/usr/bin/env python3
"""
Script para crear una nueva evaluación en estado borrador con puntaje menor a 80
"""
import os
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from planes.models import Evaluacion, Proveedor
from django.contrib.auth.models import User

def crear_evaluacion_borrador():
    """Crea una nueva evaluación de prueba en estado borrador"""

    # Obtener o crear un proveedor de prueba
    proveedor, created = Proveedor.objects.get_or_create(
        nit='900987654',
        defaults={
            'razon_social': 'Empresa Test Ltda',
            'email': 'test@empresa.com',
            'activo': True
        }
    )

    if created:
        print(f"✓ Proveedor creado: {proveedor.razon_social}")
    else:
        print(f"✓ Usando proveedor existente: {proveedor.razon_social}")

    # Obtener un técnico si existe
    tecnico = User.objects.filter(perfil__tipo_perfil='TECNICO').first()

    # Crear la evaluación en borrador con puntaje < 80
    evaluacion = Evaluacion.objects.create(
        proveedor=proveedor,
        periodo='2025-Q2',
        numero_contrato='CONT-2025-002',
        tipo_contrato='OBRA',
        subcategoria='Obras Civiles',
        tecnico_asignado=tecnico,
        puntaje=72,  # Puntaje menor a 80
        fecha=date.today(),
        fecha_limite_aclaracion=date.today() + timedelta(days=10),
        fecha_limite_plan=date.today() + timedelta(days=20),

        # Desglose de puntajes
        puntaje_gestion=18,
        puntaje_calidad=14,
        puntaje_oportunidad=20,
        puntaje_ambiental_social=10,
        puntaje_sst=10,

        # Puntajes máximos
        max_gestion=25,
        max_calidad=25,
        max_oportunidad=25,
        max_ambiental_social=12.5,
        max_sst=12.5,

        # Observaciones por criterio
        observaciones_gestion='Gestión adecuada con algunas oportunidades de mejora',
        observaciones_calidad='Calidad aceptable, se requieren mejoras',
        observaciones_oportunidad='Buen desempeño en tiempos de entrega',
        observaciones_ambiental_social='Cumplimiento parcial de normas ambientales',
        observaciones_sst='Se requiere reforzar protocolos de seguridad',
        observaciones_generales='Evaluación general: Desempeño Aceptable (72/100). Requiere Plan de Mejoramiento.',

        # Estado de firma (BORRADOR)
        estado_firma='PROCESO_FIRMAS',

        # Flujo de evaluación
        estado_flujo_evaluacion='FLUJO_NORMAL'
    )

    print(f"\n{'='*60}")
    print(f"EVALUACIÓN EN BORRADOR CREADA EXITOSAMENTE")
    print(f"{'='*60}")
    print(f"ID: {evaluacion.id}")
    print(f"Proveedor: {evaluacion.proveedor.razon_social}")
    print(f"NIT: {evaluacion.proveedor.nit}")
    print(f"Período: {evaluacion.periodo}")
    print(f"Contrato: {evaluacion.numero_contrato}")
    print(f"Tipo: {evaluacion.get_tipo_contrato_display()}")
    print(f"Puntaje: {evaluacion.puntaje}/100")
    print(f"Estado: {evaluacion.estado_evaluacion}")
    print(f"Requiere Plan: {'Sí' if evaluacion.requiere_plan() else 'No'}")
    print(f"Técnico Asignado: {evaluacion.tecnico_asignado.username if evaluacion.tecnico_asignado else 'No asignado'}")
    print(f"Fecha Evaluación: {evaluacion.fecha}")
    print(f"Fecha Límite Aclaración: {evaluacion.fecha_limite_aclaracion}")
    print(f"Fecha Límite Plan: {evaluacion.fecha_limite_plan}")
    print(f"\nDesglose de Puntajes:")
    print(f"  - Gestión: {evaluacion.puntaje_gestion}/{evaluacion.max_gestion}")
    print(f"  - Calidad: {evaluacion.puntaje_calidad}/{evaluacion.max_calidad}")
    print(f"  - Oportunidad: {evaluacion.puntaje_oportunidad}/{evaluacion.max_oportunidad}")
    print(f"  - Ambiental y Social: {evaluacion.puntaje_ambiental_social}/{evaluacion.max_ambiental_social}")
    print(f"  - SST: {evaluacion.puntaje_sst}/{evaluacion.max_sst}")
    print(f"{'='*60}")
    print(f"\n✓ Accede a: http://localhost:9040/evaluacion/{evaluacion.id}/")

    return evaluacion

if __name__ == '__main__':
    try:
        evaluacion = crear_evaluacion_borrador()
    except Exception as e:
        print(f"\n✗ Error al crear la evaluación: {str(e)}")
        import traceback
        traceback.print_exc()
