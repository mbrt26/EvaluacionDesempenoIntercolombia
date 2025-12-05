"""
Pruebas exhaustivas para todos los modelos del sistema
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from decimal import Decimal
from planes.models import (
    PerfilUsuario, Proveedor, Evaluacion, PlanMejoramiento,
    DocumentoPlan, AccionMejora, HistorialEstado, HistorialCambioCampo,
    PlanAdjunto, TipoCalificacion, CriterioEvaluacion, RespuestaEvaluacion,
    Notificacion
)


class PerfilUsuarioModelTest(TestCase):
    """Pruebas para el modelo PerfilUsuario"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_crear_perfil_usuario(self):
        """Test creación básica de perfil"""
        perfil = PerfilUsuario.objects.create(
            user=self.user,
            tipo_perfil='TECNICO'
        )
        self.assertEqual(perfil.tipo_perfil, 'TECNICO')
        self.assertTrue(perfil.activo)
        self.assertTrue(perfil.requiere_cambio_password)

    def test_propiedades_perfil(self):
        """Test propiedades de tipo de perfil"""
        perfil = PerfilUsuario.objects.create(user=self.user, tipo_perfil='TECNICO')
        self.assertTrue(perfil.es_tecnico)
        self.assertFalse(perfil.es_proveedor)
        self.assertFalse(perfil.es_gestor)
        self.assertFalse(perfil.es_gestor_compras)

    def test_str_representation(self):
        """Test representación string"""
        perfil = PerfilUsuario.objects.create(user=self.user, tipo_perfil='PROVEEDOR')
        self.assertIn('testuser', str(perfil))
        self.assertIn('Proveedor', str(perfil))

    def test_onetoone_constraint(self):
        """Test que un usuario solo puede tener un perfil"""
        PerfilUsuario.objects.create(user=self.user, tipo_perfil='TECNICO')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PerfilUsuario.objects.create(user=self.user, tipo_perfil='PROVEEDOR')


class ProveedorModelTest(TestCase):
    """Pruebas para el modelo Proveedor"""

    def test_crear_proveedor_sin_usuario(self):
        """Test crear proveedor sin usuario asociado"""
        proveedor = Proveedor.objects.create(
            nit='123456789-0',
            razon_social='Empresa Test S.A.S',
            email='empresa@test.com'
        )
        self.assertIsNone(proveedor.user)
        self.assertTrue(proveedor.activo)

    def test_crear_proveedor_con_usuario(self):
        """Test crear proveedor con usuario asociado"""
        user = User.objects.create_user(username='proveedor1', password='pass123')
        proveedor = Proveedor.objects.create(
            user=user,
            nit='987654321-0',
            razon_social='Otra Empresa S.A.',
            email='otra@empresa.com'
        )
        self.assertEqual(proveedor.user, user)

    def test_nit_unico(self):
        """Test que el NIT es único"""
        Proveedor.objects.create(
            nit='111111111-1',
            razon_social='Primera Empresa',
            email='primera@email.com'
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Proveedor.objects.create(
                    nit='111111111-1',
                    razon_social='Segunda Empresa',
                    email='segunda@email.com'
                )

    def test_str_representation(self):
        """Test representación string"""
        proveedor = Proveedor.objects.create(
            nit='222222222-2',
            razon_social='Mi Empresa',
            email='mi@empresa.com'
        )
        self.assertIn('222222222-2', str(proveedor))
        self.assertIn('Mi Empresa', str(proveedor))


class EvaluacionModelTest(TestCase):
    """Pruebas para el modelo Evaluacion"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='333333333-3',
            razon_social='Proveedor Test',
            email='proveedor@test.com'
        )
        self.user_tecnico = User.objects.create_user(
            username='tecnico1',
            password='pass123'
        )

    def test_crear_evaluacion_basica(self):
        """Test creación básica de evaluación"""
        evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-Q1',
            puntaje=85,
            fecha=date.today()
        )
        self.assertEqual(evaluacion.puntaje, 85)
        self.assertEqual(evaluacion.estado_firma, 'PROCESO_FIRMAS')
        self.assertEqual(evaluacion.estado_flujo_evaluacion, 'FLUJO_NORMAL')

    def test_estado_evaluacion_satisfactorio(self):
        """Test estado evaluación >= 80"""
        evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-Q2',
            puntaje=85,
            fecha=date.today()
        )
        self.assertEqual(evaluacion.estado_evaluacion, 'Desempeño Satisfactorio')
        self.assertFalse(evaluacion.requiere_plan())

    def test_estado_evaluacion_aceptable(self):
        """Test estado evaluación >= 60 y < 80"""
        evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-Q3',
            puntaje=70,
            fecha=date.today()
        )
        self.assertEqual(evaluacion.estado_evaluacion, 'Desempeño Aceptable')
        self.assertTrue(evaluacion.requiere_plan())

    def test_estado_evaluacion_critico(self):
        """Test estado evaluación < 60"""
        evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-Q4',
            puntaje=45,
            fecha=date.today()
        )
        self.assertEqual(evaluacion.estado_evaluacion, 'Desempeño Crítico')
        self.assertTrue(evaluacion.requiere_plan())

    def test_unique_together_proveedor_periodo(self):
        """Test restricción única proveedor-periodo"""
        Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-UNIQUE',
            puntaje=75,
            fecha=date.today()
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Evaluacion.objects.create(
                    proveedor=self.proveedor,
                    periodo='2024-UNIQUE',
                    puntaje=80,
                    fecha=date.today()
                )

    def test_puntajes_desglosados(self):
        """Test puntajes desglosados por categoría"""
        evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-DESGLOSE',
            puntaje=80,
            fecha=date.today(),
            puntaje_gestion=20,
            puntaje_calidad=20,
            puntaje_oportunidad=15,
            puntaje_ambiental_social=15,
            puntaje_sst=10
        )
        self.assertEqual(evaluacion.puntaje_gestion, 20)
        self.assertEqual(evaluacion.puntaje_calidad, 20)
        self.assertEqual(evaluacion.puntaje_oportunidad, 15)
        self.assertEqual(evaluacion.puntaje_ambiental_social, 15)
        self.assertEqual(evaluacion.puntaje_sst, 10)

    def test_tipos_contrato_validos(self):
        """Test que acepta tipos de contrato válidos"""
        for tipo, _ in Evaluacion.TIPOS_CONTRATO:
            evaluacion = Evaluacion.objects.create(
                proveedor=self.proveedor,
                periodo=f'2024-{tipo}',
                puntaje=75,
                fecha=date.today(),
                tipo_contrato=tipo
            )
            self.assertEqual(evaluacion.tipo_contrato, tipo)

    def test_sociedades_validas(self):
        """Test que acepta sociedades válidas"""
        for sociedad, _ in Evaluacion.SOCIEDADES:
            # Crear un nuevo proveedor para cada sociedad para evitar conflicto unique
            proveedor = Proveedor.objects.create(
                nit=f'SOC-{sociedad}',
                razon_social=f'Proveedor {sociedad}',
                email=f'{sociedad.lower()}@test.com'
            )
            evaluacion = Evaluacion.objects.create(
                proveedor=proveedor,
                periodo='2024-SOC',
                puntaje=75,
                fecha=date.today(),
                sociedad=sociedad
            )
            self.assertEqual(evaluacion.sociedad, sociedad)


class PlanMejoramientoModelTest(TestCase):
    """Pruebas para el modelo PlanMejoramiento"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='444444444-4',
            razon_social='Proveedor Plan Test',
            email='plan@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-PLAN',
            puntaje=65,
            fecha=date.today()
        )

    def test_crear_plan_basico(self):
        """Test creación básica de plan"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Causa raíz identificada',
            acciones_propuestas='Acciones correctivas',
            responsable='Juan Pérez',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='KPI de mejora'
        )
        self.assertEqual(plan.estado, 'BORRADOR')
        self.assertEqual(plan.numero_version, 1)
        self.assertIsNotNone(plan.fecha_limite)

    def test_save_establece_fecha_limite(self):
        """Test que save establece fecha límite automáticamente"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )
        self.assertIsNotNone(plan.fecha_limite)

    def test_cambio_estado_enviado_actualiza_fecha(self):
        """Test que cambio a ENVIADO actualiza fecha_envio"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )
        self.assertIsNone(plan.fecha_envio)
        plan.estado = 'ENVIADO'
        plan.save()
        self.assertIsNotNone(plan.fecha_envio)

    def test_cambio_estado_aprobado_actualiza_fecha(self):
        """Test que cambio a APROBADO actualiza fecha_aprobacion"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )
        plan.estado = 'APROBADO'
        plan.save()
        self.assertIsNotNone(plan.fecha_aprobacion)

    def test_dias_pendiente(self):
        """Test cálculo de días pendiente"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores',
            estado='ENVIADO'
        )
        # Con fecha_envio de hoy, días pendiente debería ser 0
        self.assertEqual(plan.dias_pendiente, 0)

    def test_dias_para_vencimiento(self):
        """Test cálculo de días para vencimiento"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores',
            fecha_limite=date.today() + timedelta(days=10)
        )
        self.assertEqual(plan.dias_para_vencimiento, 10)

    def test_esta_vencido_false(self):
        """Test plan no vencido"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores',
            fecha_limite=date.today() + timedelta(days=10)
        )
        self.assertFalse(plan.esta_vencido)

    def test_esta_vencido_true(self):
        """Test plan vencido"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores',
            fecha_limite=date.today() - timedelta(days=5)
        )
        self.assertTrue(plan.esta_vencido)

    def test_todos_estados_validos(self):
        """Test que todos los estados son válidos"""
        for estado, _ in PlanMejoramiento.ESTADOS:
            # Crear nueva evaluación para evitar problemas
            evaluacion = Evaluacion.objects.create(
                proveedor=self.proveedor,
                periodo=f'2024-EST-{estado}',
                puntaje=65,
                fecha=date.today()
            )
            plan = PlanMejoramiento.objects.create(
                evaluacion=evaluacion,
                proveedor=self.proveedor,
                analisis_causa='Análisis',
                acciones_propuestas='Acciones',
                responsable='Responsable',
                fecha_implementacion=date.today() + timedelta(days=30),
                indicadores_seguimiento='Indicadores',
                estado=estado
            )
            self.assertEqual(plan.estado, estado)


class DocumentoPlanModelTest(TestCase):
    """Pruebas para el modelo DocumentoPlan"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='555555555-5',
            razon_social='Proveedor Docs',
            email='docs@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-DOCS',
            puntaje=70,
            fecha=date.today()
        )
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )

    def test_crear_documento(self):
        """Test creación de documento"""
        doc = DocumentoPlan.objects.create(
            plan=self.plan,
            nombre='Documento de prueba',
            descripcion='Descripción del documento'
        )
        self.assertEqual(doc.nombre, 'Documento de prueba')
        self.assertIsNotNone(doc.fecha_carga)


class AccionMejoraModelTest(TestCase):
    """Pruebas para el modelo AccionMejora"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='666666666-6',
            razon_social='Proveedor Acciones',
            email='acciones@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-ACC',
            puntaje=70,
            fecha=date.today()
        )
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )

    def test_crear_accion(self):
        """Test creación de acción"""
        accion = AccionMejora.objects.create(
            plan=self.plan,
            descripcion='Acción de mejora específica',
            responsable='María García',
            fecha_compromiso=date.today() + timedelta(days=15),
            indicador='Indicador de éxito'
        )
        self.assertFalse(accion.completado)
        self.assertEqual(accion.responsable, 'María García')

    def test_completar_accion(self):
        """Test marcar acción como completada"""
        accion = AccionMejora.objects.create(
            plan=self.plan,
            descripcion='Acción de mejora',
            responsable='Responsable',
            fecha_compromiso=date.today() + timedelta(days=15),
            indicador='Indicador'
        )
        accion.completado = True
        accion.save()
        self.assertTrue(accion.completado)


class HistorialEstadoModelTest(TestCase):
    """Pruebas para el modelo HistorialEstado"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='777777777-7',
            razon_social='Proveedor Historial',
            email='historial@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-HIST',
            puntaje=70,
            fecha=date.today()
        )
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )
        self.user = User.objects.create_user(
            username='histuser',
            password='pass123'
        )

    def test_crear_historial(self):
        """Test creación de historial de estado"""
        historial = HistorialEstado.objects.create(
            plan=self.plan,
            estado_anterior='BORRADOR',
            estado_nuevo='ENVIADO',
            usuario=self.user,
            comentario='Cambio de estado'
        )
        self.assertIn('BORRADOR', str(historial))
        self.assertIn('ENVIADO', str(historial))


class HistorialCambioCampoModelTest(TestCase):
    """Pruebas para el modelo HistorialCambioCampo"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='888888888-8',
            razon_social='Proveedor Campo',
            email='campo@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-CAMPO',
            puntaje=70,
            fecha=date.today()
        )
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )
        self.user = User.objects.create_user(
            username='campouser',
            password='pass123'
        )

    def test_crear_historial_campo(self):
        """Test creación de historial de cambio de campo"""
        historial = HistorialCambioCampo.objects.create(
            plan=self.plan,
            campo='responsable',
            valor_anterior='Juan',
            valor_nuevo='María',
            usuario=self.user
        )
        self.assertEqual(historial.campo, 'responsable')
        self.assertIn('responsable', str(historial))


class TipoCalificacionModelTest(TestCase):
    """Pruebas para el modelo TipoCalificacion"""

    def test_crear_tipo_calificacion(self):
        """Test creación de tipo de calificación"""
        tipo = TipoCalificacion.objects.create(
            codigo='TIPO-001',
            nombre='Tipo de Prueba',
            descripcion='Descripción del tipo'
        )
        self.assertTrue(tipo.activo)
        self.assertEqual(str(tipo), 'Tipo de Prueba')

    def test_codigo_unico(self):
        """Test que el código es único"""
        TipoCalificacion.objects.create(
            codigo='UNICO-001',
            nombre='Primer Tipo'
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TipoCalificacion.objects.create(
                    codigo='UNICO-001',
                    nombre='Segundo Tipo'
                )


class CriterioEvaluacionModelTest(TestCase):
    """Pruebas para el modelo CriterioEvaluacion"""

    def setUp(self):
        self.tipo_calificacion = TipoCalificacion.objects.create(
            codigo='TIPO-CRITERIO',
            nombre='Tipo para Criterio'
        )

    def test_crear_criterio(self):
        """Test creación de criterio"""
        criterio = CriterioEvaluacion.objects.create(
            id_sap=1,
            descripcion_criterio='Criterio de prueba',
            id_criterio=1,
            respuesta_normal='Respuesta completa de prueba',
            respuesta_corta='Respuesta corta',
            tipo_calificacion=self.tipo_calificacion,
            puntuacion_maxima=25
        )
        self.assertTrue(criterio.activo)
        self.assertIn('Criterio de prueba', str(criterio))

    def test_unique_together_constraint(self):
        """Test restricción unique_together"""
        CriterioEvaluacion.objects.create(
            id_sap=10,
            descripcion_criterio='Criterio 1',
            id_criterio=1,
            respuesta_normal='Respuesta',
            respuesta_corta='Corta',
            tipo_calificacion=self.tipo_calificacion,
            puntuacion_maxima=25,
            sociedad='ISA'
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CriterioEvaluacion.objects.create(
                    id_sap=10,
                    descripcion_criterio='Criterio duplicado',
                    id_criterio=1,
                    respuesta_normal='Otra respuesta',
                    respuesta_corta='Otra corta',
                    tipo_calificacion=self.tipo_calificacion,
                    puntuacion_maxima=25,
                    sociedad='ISA'
                )


class RespuestaEvaluacionModelTest(TestCase):
    """Pruebas para el modelo RespuestaEvaluacion"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='999999999-9',
            razon_social='Proveedor Respuesta',
            email='respuesta@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-RESP',
            puntaje=75,
            fecha=date.today()
        )
        self.tipo_calificacion = TipoCalificacion.objects.create(
            codigo='TIPO-RESP',
            nombre='Tipo Respuesta'
        )
        self.criterio = CriterioEvaluacion.objects.create(
            id_sap=100,
            descripcion_criterio='Criterio para respuesta',
            id_criterio=1,
            respuesta_normal='Respuesta normal',
            respuesta_corta='Corta',
            tipo_calificacion=self.tipo_calificacion,
            puntuacion_maxima=25
        )

    def test_crear_respuesta(self):
        """Test creación de respuesta"""
        respuesta = RespuestaEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterio=self.criterio,
            id_criterio=1,
            puntuacion_obtenida=Decimal('20.50')
        )
        self.assertEqual(respuesta.puntuacion_obtenida, Decimal('20.50'))

    def test_unique_together_evaluacion_id_criterio(self):
        """Test restricción única evaluacion-id_criterio"""
        RespuestaEvaluacion.objects.create(
            evaluacion=self.evaluacion,
            criterio=self.criterio,
            id_criterio=1,
            puntuacion_obtenida=Decimal('20.00')
        )
        # Crear otro criterio para la segunda respuesta
        criterio2 = CriterioEvaluacion.objects.create(
            id_sap=101,
            descripcion_criterio='Criterio 2',
            id_criterio=2,
            respuesta_normal='Respuesta',
            respuesta_corta='Corta',
            tipo_calificacion=self.tipo_calificacion,
            puntuacion_maxima=25
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RespuestaEvaluacion.objects.create(
                    evaluacion=self.evaluacion,
                    criterio=criterio2,
                    id_criterio=1,  # Mismo id_criterio, diferente criterio FK
                    puntuacion_obtenida=Decimal('15.00')
                )


class NotificacionModelTest(TestCase):
    """Pruebas para el modelo Notificacion"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='notifuser',
            password='pass123'
        )
        self.proveedor = Proveedor.objects.create(
            nit='101010101-0',
            razon_social='Proveedor Notif',
            email='notif@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-NOTIF',
            puntaje=70,
            fecha=date.today()
        )
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )

    def test_crear_notificacion(self):
        """Test creación de notificación"""
        notif = Notificacion.objects.create(
            usuario=self.user,
            tipo='PLAN_ENVIADO',
            plan=self.plan,
            mensaje='El plan ha sido enviado'
        )
        self.assertFalse(notif.leida)
        self.assertEqual(notif.get_tipo_display(), 'Plan Enviado')

    def test_marcar_como_leida(self):
        """Test marcar notificación como leída"""
        notif = Notificacion.objects.create(
            usuario=self.user,
            tipo='PLAN_APROBADO',
            mensaje='Plan aprobado'
        )
        notif.leida = True
        notif.save()
        self.assertTrue(notif.leida)

    def test_todos_tipos_validos(self):
        """Test que todos los tipos son válidos"""
        for tipo, _ in Notificacion.TIPOS:
            notif = Notificacion.objects.create(
                usuario=self.user,
                tipo=tipo,
                mensaje=f'Mensaje de tipo {tipo}'
            )
            self.assertEqual(notif.tipo, tipo)


class PlanAdjuntoModelTest(TestCase):
    """Pruebas para el modelo PlanAdjunto"""

    def setUp(self):
        self.proveedor = Proveedor.objects.create(
            nit='121212121-2',
            razon_social='Proveedor Adjunto',
            email='adjunto@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-ADJ',
            puntaje=70,
            fecha=date.today()
        )
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )
        self.user = User.objects.create_user(
            username='adjuntouser',
            password='pass123'
        )

    def test_crear_adjunto(self):
        """Test creación de adjunto"""
        adjunto = PlanAdjunto.objects.create(
            plan=self.plan,
            tipo_documento='PLAN_MEJORAMIENTO',
            nombre_original='documento.pdf',
            descripcion='Documento de prueba',
            subido_por=self.user
        )
        self.assertEqual(adjunto.tipo_documento, 'PLAN_MEJORAMIENTO')

    def test_todos_tipos_documento_validos(self):
        """Test que todos los tipos de documento son válidos"""
        for tipo, _ in PlanAdjunto.TIPOS_DOCUMENTO:
            adjunto = PlanAdjunto.objects.create(
                plan=self.plan,
                tipo_documento=tipo,
                nombre_original=f'doc_{tipo}.pdf'
            )
            self.assertEqual(adjunto.tipo_documento, tipo)


class RelacionesEntreModelosTest(TestCase):
    """Pruebas de relaciones entre modelos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='reluser',
            password='pass123'
        )
        self.proveedor = Proveedor.objects.create(
            user=self.user,
            nit='131313131-3',
            razon_social='Proveedor Relaciones',
            email='relaciones@test.com'
        )
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-REL',
            puntaje=70,
            fecha=date.today()
        )
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            analisis_causa='Análisis',
            acciones_propuestas='Acciones',
            responsable='Responsable',
            fecha_implementacion=date.today() + timedelta(days=30),
            indicadores_seguimiento='Indicadores'
        )

    def test_proveedor_tiene_evaluaciones(self):
        """Test relación proveedor -> evaluaciones"""
        self.assertEqual(self.proveedor.evaluaciones.count(), 1)
        self.assertEqual(self.proveedor.evaluaciones.first(), self.evaluacion)

    def test_proveedor_tiene_planes(self):
        """Test relación proveedor -> planes_mejoramiento"""
        self.assertEqual(self.proveedor.planes_mejoramiento.count(), 1)
        self.assertEqual(self.proveedor.planes_mejoramiento.first(), self.plan)

    def test_evaluacion_tiene_planes(self):
        """Test relación evaluacion -> planes"""
        self.assertEqual(self.evaluacion.planes.count(), 1)
        self.assertEqual(self.evaluacion.planes.first(), self.plan)

    def test_plan_tiene_documentos(self):
        """Test relación plan -> documentos"""
        DocumentoPlan.objects.create(
            plan=self.plan,
            nombre='Doc 1'
        )
        DocumentoPlan.objects.create(
            plan=self.plan,
            nombre='Doc 2'
        )
        self.assertEqual(self.plan.documentos.count(), 2)

    def test_plan_tiene_acciones(self):
        """Test relación plan -> acciones"""
        AccionMejora.objects.create(
            plan=self.plan,
            descripcion='Acción 1',
            responsable='Resp 1',
            fecha_compromiso=date.today() + timedelta(days=10),
            indicador='Ind 1'
        )
        AccionMejora.objects.create(
            plan=self.plan,
            descripcion='Acción 2',
            responsable='Resp 2',
            fecha_compromiso=date.today() + timedelta(days=20),
            indicador='Ind 2'
        )
        self.assertEqual(self.plan.acciones.count(), 2)

    def test_plan_tiene_historial(self):
        """Test relación plan -> historial"""
        HistorialEstado.objects.create(
            plan=self.plan,
            estado_anterior='BORRADOR',
            estado_nuevo='ENVIADO',
            usuario=self.user
        )
        self.assertEqual(self.plan.historial.count(), 1)

    def test_plan_tiene_adjuntos(self):
        """Test relación plan -> adjuntos"""
        PlanAdjunto.objects.create(
            plan=self.plan,
            tipo_documento='OTRO',
            nombre_original='adjunto.pdf'
        )
        self.assertEqual(self.plan.adjuntos.count(), 1)

    def test_user_tiene_perfil(self):
        """Test relación user -> perfil"""
        PerfilUsuario.objects.create(
            user=self.user,
            tipo_perfil='PROVEEDOR'
        )
        self.assertEqual(self.user.perfil.tipo_perfil, 'PROVEEDOR')

    def test_user_tiene_proveedor(self):
        """Test relación user -> proveedor"""
        self.assertEqual(self.user.proveedor, self.proveedor)

    def test_cascade_delete_proveedor(self):
        """Test que eliminar proveedor elimina evaluaciones y planes"""
        proveedor_id = self.proveedor.id
        evaluacion_id = self.evaluacion.id
        plan_id = self.plan.id

        self.proveedor.delete()

        self.assertFalse(Proveedor.objects.filter(id=proveedor_id).exists())
        self.assertFalse(Evaluacion.objects.filter(id=evaluacion_id).exists())
        self.assertFalse(PlanMejoramiento.objects.filter(id=plan_id).exists())
