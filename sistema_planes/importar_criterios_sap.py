#!/usr/bin/env python3
"""
Script para importar criterios de evaluación desde el archivo Excel de SAP
"""
import os
import sys
import django
import pandas as pd

# Configurar Django
sys.path.append('/home/mrodriguez/proyectos/EvaluacionDesempenoIntercolombia/sistema_planes')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from planes.models import TipoCalificacion, CriterioEvaluacion

def limpiar_texto(texto):
    """Limpia y normaliza el texto"""
    if pd.isna(texto):
        return ""
    return str(texto).strip()

def importar_criterios():
    """Importa los criterios desde el archivo Excel"""

    # Ruta al archivo Excel
    archivo_excel = "/home/mrodriguez/proyectos/EvaluacionDesempenoIntercolombia/Ajustes/Ponderacion Evaluacion en SAP (1).xlsx"

    print("📂 Leyendo archivo Excel...")
    df = pd.read_excel(archivo_excel, sheet_name="SAP")

    # Configurar nombres de columnas
    df.columns = ['id_sap', 'descripcion_criterio', 'id_criterio', 'respuesta_normal',
                  'respuesta_corta', 'sociedad', 'tipo_calificacion', 'puntuacion']

    # Eliminar primera fila (encabezados duplicados)
    df = df[1:]

    # Limpiar datos
    df = df.dropna(subset=['tipo_calificacion', 'id_criterio'])

    print(f"✅ Archivo leído: {len(df)} registros encontrados")

    # Confirmar antes de borrar datos existentes
    print("\n⚠️  ADVERTENCIA: Este proceso eliminará todos los criterios existentes.")
    respuesta = input("¿Desea continuar? (si/no): ")

    if respuesta.lower() != 'si':
        print("❌ Operación cancelada")
        return

    # Eliminar criterios existentes
    print("\n🗑️  Eliminando criterios existentes...")
    CriterioEvaluacion.objects.all().delete()
    print("✅ Criterios eliminados")

    # Procesar tipos de calificación
    tipos_calificacion = {}
    tipos_unicos = df['tipo_calificacion'].unique()

    print(f"\n📋 Procesando {len(tipos_unicos)} tipos de calificación...")

    for tipo_nombre in tipos_unicos:
        if pd.isna(tipo_nombre):
            continue

        tipo_nombre = limpiar_texto(tipo_nombre)

        # Buscar o crear tipo de calificación
        tipo_obj, created = TipoCalificacion.objects.get_or_create(
            nombre=tipo_nombre,
            defaults={
                'descripcion': f'Tipo de calificación para {tipo_nombre}',
                'activo': True
            }
        )
        tipos_calificacion[tipo_nombre] = tipo_obj

        if created:
            print(f"  ✅ Creado: {tipo_nombre}")
        else:
            print(f"  ♻️  Actualizado: {tipo_nombre}")

    # Importar criterios
    print(f"\n📊 Importando {len(df)} criterios...")

    criterios_creados = 0
    errores = 0

    for idx, row in df.iterrows():
        try:
            tipo_nombre = limpiar_texto(row['tipo_calificacion'])

            if not tipo_nombre or tipo_nombre not in tipos_calificacion:
                continue

            tipo_obj = tipos_calificacion[tipo_nombre]

            # Crear criterio
            criterio = CriterioEvaluacion.objects.create(
                id_sap=int(row['id_sap']),
                tipo_calificacion=tipo_obj,
                id_criterio=int(row['id_criterio']),
                descripcion_criterio=limpiar_texto(row['descripcion_criterio']),
                respuesta_normal=limpiar_texto(row['respuesta_normal']),
                respuesta_corta=limpiar_texto(row['respuesta_corta']),
                sociedad=limpiar_texto(row['sociedad']),
                puntuacion_maxima=float(row['puntuacion']),
                activo=True
            )

            criterios_creados += 1

            if criterios_creados % 50 == 0:
                print(f"  📝 {criterios_creados} criterios importados...")

        except Exception as e:
            errores += 1
            print(f"  ❌ Error en fila {idx}: {e}")

    print(f"\n{'='*60}")
    print(f"✅ IMPORTACIÓN COMPLETADA")
    print(f"{'='*60}")
    print(f"📋 Tipos de calificación: {len(tipos_calificacion)}")
    print(f"📊 Criterios creados: {criterios_creados}")
    print(f"❌ Errores: {errores}")
    print(f"{'='*60}")

    # Mostrar resumen por tipo
    print("\n📈 RESUMEN POR TIPO DE CALIFICACIÓN:")
    for tipo_nombre, tipo_obj in tipos_calificacion.items():
        cantidad = CriterioEvaluacion.objects.filter(tipo_calificacion=tipo_obj).count()
        print(f"  • {tipo_nombre}: {cantidad} criterios")

if __name__ == '__main__':
    try:
        importar_criterios()
    except KeyboardInterrupt:
        print("\n\n❌ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
