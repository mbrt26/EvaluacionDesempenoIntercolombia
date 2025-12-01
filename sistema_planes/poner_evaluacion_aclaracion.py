#!/usr/bin/env python3
"""
Script para poner una evaluación en estado de aclaración
"""
import os
import django
from datetime import date
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from planes.models import Evaluacion

def poner_en_aclaracion(evaluacion_id):
    """Pone una evaluación en estado de aclaración"""
    try:
        evaluacion = Evaluacion.objects.get(id=evaluacion_id)

        print(f"Evaluación ID: {evaluacion_id}")
        print(f"Estado actual: {evaluacion.get_estado_flujo_evaluacion_display()}")

        # Cambiar al estado de aclaración
        evaluacion.estado_flujo_evaluacion = 'ACLARACION'
        evaluacion.fecha_cambio_estado_flujo = timezone.now()
        evaluacion.observaciones_flujo = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Proveedor solicita aclaración de la evaluación"
        evaluacion.save()

        print(f"Nuevo estado: {evaluacion.get_estado_flujo_evaluacion_display()}")
        print(f"Puntaje: {evaluacion.puntaje}/100")
        print(f"\n✓ Evaluación actualizada a estado ACLARACION")
        print(f"\nAhora puedes ver la evaluación en: http://localhost:9040/evaluacion/{evaluacion_id}/")

    except Evaluacion.DoesNotExist:
        print(f"✗ No se encontró la evaluación con ID {evaluacion_id}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    poner_en_aclaracion(69)
