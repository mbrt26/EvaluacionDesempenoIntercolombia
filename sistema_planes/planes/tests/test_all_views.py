"""
Testing Automatizado de Todas las Vistas del Proyecto
Implementa pruebas exhaustivas para cada vista con diferentes niveles de testing
"""

from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from planes.models import Proveedor, Evaluacion, PlanMejoramiento, AccionMejora
from datetime import date, timedelta
from django.utils import timezone
import json


class AllViewsTestCase(TransactionTestCase):
    """
    Suite completa de tests para todas las vistas del sistema
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        print("\n" + "="*60)
        print("🧪 INICIANDO SUITE DE TESTS AUTOMATIZADOS")
        print("="*60)
        
    def setUp(self):
        """Configurar datos de prueba para cada test"""
        # Cliente de prueba
        self.client = Client()
        
        # Crear usuarios de prueba
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            password='admin123',
            email='admin@test.com'
        )
        
        self.tecnico_user = User.objects.create_user(
            username='tecnico_test',
            password='tecnico123',
            email='tecnico@test.com',
            first_name='Carlos',
            last_name='Técnico'
        )
        
        self.proveedor_user = User.objects.create_user(
            username='900123456',
            password='proveedor123',
            email='proveedor@test.com'
        )
        
        # Crear proveedor
        self.proveedor = Proveedor.objects.create(
            user=self.proveedor_user,
            nit='900.123.456-7',
            razon_social='Empresa Test S.A.S.',
            email='empresa@test.com',
            telefono='3001234567'
        )
        
        # Crear evaluación
        self.evaluacion = Evaluacion.objects.create(
            proveedor=self.proveedor,
            periodo='2024-Q1',
            puntaje=65,
            fecha=date.today(),
            puntaje_calidad=70,
            puntaje_entrega=60,
            puntaje_documentacion=65,
            puntaje_precio=75,
            observaciones='Evaluación de prueba'
        )
        
        # Crear plan de mejoramiento
        self.plan = PlanMejoramiento.objects.create(
            evaluacion=self.evaluacion,
            proveedor=self.proveedor,
            estado='ENVIADO',
            analisis_causa='Análisis de prueba',
            acciones_propuestas='Acciones de prueba',
            responsable='Gerente de Calidad',
            fecha_implementacion=date.today() + timedelta(days=90),
            indicadores_seguimiento='Indicadores de prueba',
            fecha_envio=timezone.now()
        )
        
        # Crear acción de mejora
        self.accion = AccionMejora.objects.create(
            plan=self.plan,
            descripcion='Acción de prueba',
            responsable='Responsable Test',
            fecha_compromiso=date.today() + timedelta(days=30),
            indicador='Indicador de prueba'
        )
        
    def tearDown(self):
        """Limpiar después de cada test"""
        self.client.logout()
        
    # ===================== TESTS DE VISTAS PÚBLICAS =====================
    
    def test_01_login_view(self):
        """Test de la vista de login"""
        print("\n📍 Testing: Vista de Login")
        
        # GET - Debe mostrar el formulario
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sistema de Planes de Mejoramiento')
        print("   ✅ GET / -> 200 OK")
        
        # POST - Login exitoso como proveedor
        response = self.client.post('/', {
            'username': '900123456',
            'password': 'proveedor123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/dashboard/')
        print("   ✅ POST / (proveedor) -> Redirect a dashboard")
        
        # Logout
        self.client.logout()
        
        # POST - Login exitoso como técnico
        response = self.client.post('/', {
            'username': 'tecnico_test',
            'password': 'tecnico123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/panel-tecnico/')
        print("   ✅ POST / (técnico) -> Redirect a panel técnico")
        
        # POST - Login fallido
        response = self.client.post('/', {
            'username': 'usuario_invalido',
            'password': 'password_invalida'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos')
        print("   ✅ POST / (credenciales inválidas) -> Muestra error")
        
    def test_02_logout_view(self):
        """Test de la vista de logout"""
        print("\n📍 Testing: Vista de Logout")
        
        # Login primero
        self.client.login(username='900123456', password='proveedor123')
        
        # Logout
        response = self.client.get('/logout/', follow=True)
        self.assertRedirects(response, '/')
        print("   ✅ GET /logout/ -> Redirect a login")
        
    # ===================== TESTS DE VISTAS DE PROVEEDOR =====================
    
    def test_03_dashboard_proveedor(self):
        """Test del dashboard del proveedor"""
        print("\n📍 Testing: Dashboard Proveedor")
        
        # Sin autenticación - debe redirigir
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        print("   ✅ GET /dashboard/ (sin auth) -> 302 Redirect")
        
        # Con autenticación
        self.client.login(username='900123456', password='proveedor123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Empresa Test S.A.S.')
        self.assertContains(response, '65')  # Puntaje
        print("   ✅ GET /dashboard/ (con auth) -> 200 OK")
        
    def test_04_crear_plan(self):
        """Test de creación de plan de mejoramiento"""
        print("\n📍 Testing: Crear Plan")
        
        # Login como proveedor
        self.client.login(username='900123456', password='proveedor123')
        
        # Eliminar plan existente para poder crear uno nuevo
        PlanMejoramiento.objects.filter(evaluacion=self.evaluacion).delete()
        
        # GET - Formulario de creación
        response = self.client.get(f'/crear-plan/{self.evaluacion.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear Plan de Mejoramiento')
        print(f"   ✅ GET /crear-plan/{self.evaluacion.id}/ -> 200 OK")
        
        # POST - Crear plan
        response = self.client.post(f'/crear-plan/{self.evaluacion.id}/', {
            'analisis_causa': 'Análisis detallado de las causas raíz del problema',
            'acciones_propuestas': 'Acciones concretas para mejorar',
            'responsable': 'Gerente de Operaciones',
            'fecha_implementacion': (date.today() + timedelta(days=60)).isoformat(),
            'indicadores': 'KPIs de seguimiento',
            'accion_1': 'Primera acción de mejora',
            'responsable_1': 'Jefe de Calidad',
            'fecha_1': (date.today() + timedelta(days=30)).isoformat(),
            'indicador_1': 'Indicador 1'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PlanMejoramiento.objects.filter(
            evaluacion=self.evaluacion,
            estado='ENVIADO'
        ).exists())
        print(f"   ✅ POST /crear-plan/{self.evaluacion.id}/ -> Plan creado")
        
    def test_05_ver_plan(self):
        """Test de visualización de plan"""
        print("\n📍 Testing: Ver Plan")
        
        # Login como proveedor
        self.client.login(username='900123456', password='proveedor123')
        
        # Ver plan
        response = self.client.get(f'/ver-plan/{self.plan.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Plan de Mejoramiento')
        self.assertContains(response, 'Análisis de prueba')
        print(f"   ✅ GET /ver-plan/{self.plan.id}/ -> 200 OK")
        
    def test_06_editar_plan(self):
        """Test de edición de plan"""
        print("\n📍 Testing: Editar Plan")
        
        # Login como proveedor
        self.client.login(username='900123456', password='proveedor123')
        
        # Cambiar estado a REQUIERE_AJUSTES para poder editar
        self.plan.estado = 'REQUIERE_AJUSTES'
        self.plan.comentarios_tecnico = 'Necesita más detalle'
        self.plan.save()
        
        # GET - Formulario de edición
        response = self.client.get(f'/editar-plan/{self.plan.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Plan')
        self.assertContains(response, 'Necesita más detalle')
        print(f"   ✅ GET /editar-plan/{self.plan.id}/ -> 200 OK")
        
        # POST - Guardar cambios
        response = self.client.post(f'/editar-plan/{self.plan.id}/', {
            'analisis_causa': 'Análisis actualizado con más detalle',
            'acciones_propuestas': 'Acciones actualizadas',
            'responsable': 'Gerente General',
            'fecha_implementacion': (date.today() + timedelta(days=90)).isoformat(),
            'indicadores': 'Indicadores actualizados',
            'accion_1': 'Acción actualizada',
            'responsable_1': 'Nuevo responsable',
            'fecha_1': (date.today() + timedelta(days=45)).isoformat(),
            'indicador_1': 'Indicador actualizado'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        plan_actualizado = PlanMejoramiento.objects.get(id=self.plan.id)
        self.assertEqual(plan_actualizado.estado, 'ENVIADO')
        self.assertEqual(plan_actualizado.numero_version, 2)
        print(f"   ✅ POST /editar-plan/{self.plan.id}/ -> Plan actualizado")
        
    # ===================== TESTS DE VISTAS DE TÉCNICO =====================
    
    def test_07_panel_tecnico(self):
        """Test del panel del técnico"""
        print("\n📍 Testing: Panel Técnico")
        
        # Sin autenticación
        response = self.client.get('/panel-tecnico/')
        self.assertEqual(response.status_code, 302)
        print("   ✅ GET /panel-tecnico/ (sin auth) -> 302 Redirect")
        
        # Con autenticación de proveedor (no debe permitir)
        self.client.login(username='900123456', password='proveedor123')
        response = self.client.get('/panel-tecnico/')
        self.assertEqual(response.status_code, 302)
        print("   ✅ GET /panel-tecnico/ (proveedor) -> 302 Redirect")
        
        # Con autenticación de técnico
        self.client.logout()
        self.client.login(username='tecnico_test', password='tecnico123')
        response = self.client.get('/panel-tecnico/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel de Control')
        print("   ✅ GET /panel-tecnico/ (técnico) -> 200 OK")
        
    def test_08_revisar_plan(self):
        """Test de revisión de plan por técnico"""
        print("\n📍 Testing: Revisar Plan")
        
        # Login como técnico
        self.client.login(username='tecnico_test', password='tecnico123')
        
        # GET - Formulario de revisión
        response = self.client.get(f'/revisar-plan/{self.plan.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Revisar Plan')
        self.assertContains(response, 'Empresa Test S.A.S.')
        print(f"   ✅ GET /revisar-plan/{self.plan.id}/ -> 200 OK")
        
        # POST - Aprobar plan
        response = self.client.post(f'/revisar-plan/{self.plan.id}/', {
            'decision': 'APROBADO',
            'comentarios': 'Plan aprobado, cumple con todos los requisitos'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        plan_revisado = PlanMejoramiento.objects.get(id=self.plan.id)
        self.assertEqual(plan_revisado.estado, 'APROBADO')
        self.assertIsNotNone(plan_revisado.fecha_aprobacion)
        print(f"   ✅ POST /revisar-plan/{self.plan.id}/ -> Plan aprobado")
        
    def test_09_lista_proveedores(self):
        """Test de lista de proveedores"""
        print("\n📍 Testing: Lista de Proveedores")
        
        # Login como técnico
        self.client.login(username='tecnico_test', password='tecnico123')
        
        # GET - Lista sin filtros
        response = self.client.get('/lista-proveedores/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lista de Proveedores')
        self.assertContains(response, 'Empresa Test S.A.S.')
        print("   ✅ GET /lista-proveedores/ -> 200 OK")
        
        # GET - Con filtro de búsqueda
        response = self.client.get('/lista-proveedores/?buscar=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Empresa Test S.A.S.')
        print("   ✅ GET /lista-proveedores/?buscar=Test -> Filtro funciona")
        
        # GET - Con filtro de período
        response = self.client.get('/lista-proveedores/?periodo=2024-Q1')
        self.assertEqual(response.status_code, 200)
        print("   ✅ GET /lista-proveedores/?periodo=2024-Q1 -> Filtro funciona")
        
    # ===================== TESTS DE ADMIN =====================
    
    def test_10_admin_views(self):
        """Test de vistas del admin de Django"""
        print("\n📍 Testing: Admin Django")
        
        # Login como admin
        self.client.login(username='admin_test', password='admin123')
        
        admin_urls = [
            '/admin/',
            '/admin/auth/',
            '/admin/auth/user/',
            '/admin/planes/',
            '/admin/planes/proveedor/',
            '/admin/planes/evaluacion/',
            '/admin/planes/planmejoramiento/',
        ]
        
        for url in admin_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 301, 302])
            print(f"   ✅ GET {url} -> {response.status_code}")
            
    # ===================== TESTS DE SEGURIDAD =====================
    
    def test_11_security_access_control(self):
        """Test de control de acceso y seguridad"""
        print("\n📍 Testing: Control de Acceso")
        
        # Intentar acceder a plan de otro proveedor
        otro_user = User.objects.create_user(
            username='900999999',
            password='otro123'
        )
        otro_proveedor = Proveedor.objects.create(
            user=otro_user,
            nit='900.999.999-9',
            razon_social='Otra Empresa',
            email='otra@test.com',
            telefono='3009999999'
        )
        
        # Login como proveedor original
        self.client.login(username='900123456', password='proveedor123')
        
        # Intentar ver plan de otro proveedor (debe denegar)
        otra_evaluacion = Evaluacion.objects.create(
            proveedor=otro_proveedor,
            periodo='2024-Q1',
            puntaje=70,
            fecha=date.today()
        )
        otro_plan = PlanMejoramiento.objects.create(
            evaluacion=otra_evaluacion,
            proveedor=otro_proveedor,
            estado='ENVIADO',
            analisis_causa='Otro análisis',
            acciones_propuestas='Otras acciones',
            responsable='Otro responsable',
            fecha_implementacion=date.today() + timedelta(days=90),
            indicadores_seguimiento='Otros indicadores'
        )
        
        response = self.client.get(f'/ver-plan/{otro_plan.id}/')
        self.assertIn(response.status_code, [403, 404, 302])
        print(f"   ✅ Acceso denegado a plan de otro proveedor -> {response.status_code}")
        
    def test_12_csrf_protection(self):
        """Test de protección CSRF"""
        print("\n📍 Testing: Protección CSRF")
        
        # Login
        self.client.login(username='900123456', password='proveedor123')
        
        # Intentar POST sin CSRF token
        client_no_csrf = Client(enforce_csrf_checks=True)
        client_no_csrf.login(username='900123456', password='proveedor123')
        
        response = client_no_csrf.post(f'/crear-plan/{self.evaluacion.id}/', {
            'analisis_causa': 'Test',
            'acciones_propuestas': 'Test',
            'responsable': 'Test',
            'fecha_implementacion': date.today().isoformat(),
            'indicadores': 'Test'
        })
        
        # Debe fallar sin CSRF
        self.assertEqual(response.status_code, 403)
        print("   ✅ POST sin CSRF token -> 403 Forbidden")
        
    # ===================== TESTS DE RENDIMIENTO =====================
    
    def test_13_performance_dashboard(self):
        """Test básico de rendimiento del dashboard"""
        print("\n📍 Testing: Rendimiento")
        
        import time
        
        # Login
        self.client.login(username='900123456', password='proveedor123')
        
        # Medir tiempo de respuesta
        start_time = time.time()
        response = self.client.get('/dashboard/')
        end_time = time.time()
        
        response_time = end_time - start_time
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 2.0)  # Debe responder en menos de 2 segundos
        print(f"   ✅ Dashboard carga en {response_time:.2f} segundos")
        
    # ===================== RESUMEN DE TESTS =====================
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        print("\n" + "="*60)
        print("✅ SUITE DE TESTS COMPLETADA")
        print("="*60)