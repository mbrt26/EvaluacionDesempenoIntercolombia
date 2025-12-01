"""
Comando de Django para cargar criterios de evaluación desde Excel SAP
Uso: python manage.py cargar_criterios_sap
"""
from django.core.management.base import BaseCommand
from django.db import transaction
import pandas as pd
import os
from planes.models import TipoCalificacion, CriterioEvaluacion


class Command(BaseCommand):
    help = 'Carga criterios de evaluación desde el archivo Excel de SAP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/home/mrodriguez/proyectos/EvaluacionDesempenoIntercolombia/Ajustes/Ponderacion Evaluacion en SAP (1).xlsx',
            help='Ruta del archivo Excel'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar datos existentes antes de cargar'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_data = options['clear']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'Archivo no encontrado: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Leyendo archivo: {file_path}'))

        try:
            # Leer Excel (header en fila 1)
            df = pd.read_excel(file_path, header=1)

            self.stdout.write(self.style.SUCCESS(f'Total de filas leídas: {len(df)}'))

            # Validar columnas
            required_columns = [
                'ID SAP', 'descripcion del criterio', 'Id criterio',
                'Respuesta normal', 'Respuesta corta', 'Sociedad',
                'Tipo de calificacion', 'Puntuación'
            ]

            for col in required_columns:
                if col not in df.columns:
                    self.stdout.write(self.style.ERROR(f'Columna faltante: {col}'))
                    return

            # Limpiar datos si se solicita
            if clear_data:
                self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
                with transaction.atomic():
                    CriterioEvaluacion.objects.all().delete()
                    TipoCalificacion.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Datos eliminados'))

            # Obtener tipos únicos
            tipos_unicos = df['Tipo de calificacion'].unique()
            self.stdout.write(self.style.SUCCESS(f'Tipos de calificación encontrados: {len(tipos_unicos)}'))

            # Crear tipos de calificación
            tipos_creados = 0
            tipos_dict = {}

            with transaction.atomic():
                for tipo_nombre in tipos_unicos:
                    if pd.isna(tipo_nombre):
                        continue

                    tipo_codigo = tipo_nombre.strip().upper().replace(' ', '_')

                    tipo_obj, created = TipoCalificacion.objects.get_or_create(
                        codigo=tipo_codigo,
                        defaults={
                            'nombre': tipo_nombre.strip(),
                            'descripcion': f'Evaluación tipo: {tipo_nombre}',
                            'activo': True
                        }
                    )

                    tipos_dict[tipo_nombre.strip()] = tipo_obj

                    if created:
                        tipos_creados += 1

            self.stdout.write(self.style.SUCCESS(f'Tipos de calificación creados: {tipos_creados}'))

            # Crear criterios
            criterios_creados = 0
            criterios_actualizados = 0
            errores = 0

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Validar datos obligatorios
                        if pd.isna(row['ID SAP']) or pd.isna(row['Tipo de calificacion']):
                            continue

                        tipo_nombre = str(row['Tipo de calificacion']).strip()
                        tipo_obj = tipos_dict.get(tipo_nombre)

                        if not tipo_obj:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Tipo no encontrado para fila {index}: {tipo_nombre}'
                                )
                            )
                            continue

                        # Preparar datos
                        criterio_data = {
                            'id_sap': int(row['ID SAP']),
                            'descripcion_criterio': str(row['descripcion del criterio'])[:500],
                            'id_criterio': int(row['Id criterio']),
                            'respuesta_normal': str(row['Respuesta normal']) if not pd.isna(row['Respuesta normal']) else '',
                            'respuesta_corta': str(row['Respuesta corta'])[:500] if not pd.isna(row['Respuesta corta']) else '',
                            'sociedad': str(row['Sociedad']) if not pd.isna(row['Sociedad']) else 'ISA',
                            'puntuacion_maxima': int(row['Puntuación']),
                            'orden': index,
                            'activo': True,
                        }

                        # Crear o actualizar criterio
                        criterio, created = CriterioEvaluacion.objects.update_or_create(
                            id_sap=criterio_data['id_sap'],
                            tipo_calificacion=tipo_obj,
                            id_criterio=criterio_data['id_criterio'],
                            puntuacion_maxima=criterio_data['puntuacion_maxima'],
                            defaults=criterio_data
                        )

                        if created:
                            criterios_creados += 1
                        else:
                            criterios_actualizados += 1

                    except Exception as e:
                        errores += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error en fila {index}: {str(e)}'
                            )
                        )

            # Resumen
            self.stdout.write(self.style.SUCCESS('\n' + '='*50))
            self.stdout.write(self.style.SUCCESS('RESUMEN DE CARGA'))
            self.stdout.write(self.style.SUCCESS('='*50))
            self.stdout.write(self.style.SUCCESS(f'Tipos de calificación: {tipos_creados} creados'))
            self.stdout.write(self.style.SUCCESS(f'Criterios creados: {criterios_creados}'))
            self.stdout.write(self.style.SUCCESS(f'Criterios actualizados: {criterios_actualizados}'))
            if errores > 0:
                self.stdout.write(self.style.WARNING(f'Errores: {errores}'))
            self.stdout.write(self.style.SUCCESS('='*50))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error general: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
