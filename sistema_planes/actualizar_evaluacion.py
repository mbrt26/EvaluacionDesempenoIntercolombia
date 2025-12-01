#!/usr/bin/env python3
"""
Script para actualizar puntaje de evaluación
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from planes.models import Evaluacion

def actualizar_evaluacion(evaluacion_id, nuevo_puntaje):
    """Actualiza el puntaje de una evaluación"""

    try:
        evaluacion = Evaluacion.objects.get(id=evaluacion_id)

        print(f"Evaluación ID: {evaluacion_id}")
        print(f"Puntaje anterior: {evaluacion.puntaje}")

        # Actualizar puntaje total
        evaluacion.puntaje = nuevo_puntaje

        # Ajustar desglose proporcional
        factor = nuevo_puntaje / 100
        evaluacion.puntaje_gestion = int(evaluacion.max_gestion * factor * 0.6)  # 60% del máximo
        evaluacion.puntaje_calidad = int(evaluacion.max_calidad * factor * 0.48)  # 48% del máximo
        evaluacion.puntaje_oportunidad = int(evaluacion.max_oportunidad * factor * 0.72)  # 72% del máximo
        evaluacion.puntaje_ambiental_social = int(evaluacion.max_ambiental_social * factor * 0.8)  # 80% del máximo
        evaluacion.puntaje_sst = int(evaluacion.max_sst * factor * 0.8)  # 80% del máximo

        evaluacion.save()

        print(f"Puntaje nuevo: {evaluacion.puntaje}")
        print(f"Estado: {evaluacion.estado_evaluacion}")
        print(f"Requiere Plan: {'Sí' if evaluacion.requiere_plan() else 'No'}")
        print(f"\nDesglose actualizado:")
        print(f"  - Gestión: {evaluacion.puntaje_gestion}/{evaluacion.max_gestion}")
        print(f"  - Calidad: {evaluacion.puntaje_calidad}/{evaluacion.max_calidad}")
        print(f"  - Oportunidad: {evaluacion.puntaje_oportunidad}/{evaluacion.max_oportunidad}")
        print(f"  - Ambiental y Social: {evaluacion.puntaje_ambiental_social}/{evaluacion.max_ambiental_social}")
        print(f"  - SST: {evaluacion.puntaje_sst}/{evaluacion.max_sst}")
        print(f"\n✓ Evaluación actualizada exitosamente")

    except Evaluacion.DoesNotExist:
        print(f"✗ No se encontró la evaluación con ID {evaluacion_id}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == '__main__':
    # Actualizar evaluación 69 con puntaje menor a 80
    actualizar_evaluacion(69, 65)
