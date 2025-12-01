"""
Utilidades para Testing Automatizado
Funciones auxiliares y factories para generar datos de prueba
"""

from django.contrib.auth.models import User
from django.test import Client
from planes.models import Proveedor, Evaluacion, PlanMejoramiento, AccionMejora, DocumentoPlan
from datetime import date, timedelta
from django.utils import timezone
import random
import string
from typing import Dict, Optional, Tuple


class TestDataFactory:
    """Factory para crear datos de prueba consistentes"""
    
    @staticmethod
    def create_test_user(username: str = None, password: str = 'test123', **kwargs) -> User:
        """Crea un usuario de prueba"""
        if not username:
            username = f"test_user_{''.join(random.choices(string.ascii_lowercase, k=5))}"
            
        defaults = {
            'email': f'{username}@test.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        defaults.update(kwargs)
        
        user = User.objects.create_user(
            username=username,
            password=password,
            **defaults
        )
        return user
        
    @staticmethod
    def create_test_proveedor(nit: str = None, user: User = None) -> Tuple[User, Proveedor]:
        """Crea un proveedor de prueba con su usuario"""
        if not nit:
            nit = f"900{random.randint(100000, 999999)}"
            
        if not user:
            user = TestDataFactory.create_test_user(
                username=nit,
                password='proveedor123'
            )
            
        proveedor = Proveedor.objects.create(
            user=user,
            nit=f"{nit[:3]}.{nit[3:6]}.{nit[6:]}-{random.randint(1, 9)}",
            razon_social=f"Empresa Test {nit} S.A.S.",
            email=f"empresa_{nit}@test.com",
            telefono=f"300{random.randint(1000000, 9999999)}"
        )
        
        return user, proveedor
        
    @staticmethod
    def create_test_evaluacion(
        proveedor: Proveedor,
        puntaje: int = None,
        periodo: str = None
    ) -> Evaluacion:
        """Crea una evaluación de prueba"""
        if puntaje is None:
            puntaje = random.randint(50, 100)
            
        if periodo is None:
            periodo = f"{date.today().year}-Q{(date.today().month-1)//3 + 1}"
            
        evaluacion = Evaluacion.objects.create(
            proveedor=proveedor,
            periodo=periodo,
            puntaje=puntaje,
            fecha=date.today(),
            puntaje_calidad=random.randint(60, 100),
            puntaje_entrega=random.randint(60, 100),
            puntaje_documentacion=random.randint(60, 100),
            puntaje_precio=random.randint(60, 100),
            observaciones=f"Evaluación de prueba para {proveedor.razon_social}"
        )
        
        return evaluacion
        
    @staticmethod
    def create_test_plan(
        evaluacion: Evaluacion,
        estado: str = 'ENVIADO'
    ) -> PlanMejoramiento:
        """Crea un plan de mejoramiento de prueba"""
        plan = PlanMejoramiento.objects.create(
            evaluacion=evaluacion,
            proveedor=evaluacion.proveedor,
            estado=estado,
            analisis_causa="""
            Análisis de causa raíz de prueba:
            1. Falta de procedimientos estandarizados
            2. Capacitación insuficiente del personal
            3. Sistemas de control inadecuados
            """,
            acciones_propuestas="""
            Acciones propuestas de prueba:
            - Implementar sistema de gestión de calidad
            - Capacitar al personal
            - Establecer KPIs de seguimiento
            """,
            responsable="Gerente de Calidad Test",
            fecha_implementacion=date.today() + timedelta(days=90),
            indicadores_seguimiento="""
            Indicadores de prueba:
            - Reducción del 30% en tiempos
            - Aumento del 25% en satisfacción
            - Cero no conformidades críticas
            """,
            fecha_envio=timezone.now() if estado != 'BORRADOR' else None
        )
        
        # Crear acciones de mejora
        for i in range(3):
            AccionMejora.objects.create(
                plan=plan,
                descripcion=f"Acción de mejora {i+1}",
                responsable=f"Responsable {i+1}",
                fecha_compromiso=date.today() + timedelta(days=30*(i+1)),
                indicador=f"Indicador {i+1}"
            )
            
        return plan
        
    @staticmethod
    def create_complete_test_scenario() -> Dict:
        """Crea un escenario completo de prueba con todos los objetos necesarios"""
        # Crear admin
        admin = User.objects.create_superuser(
            username='admin_test_complete',
            password='admin123',
            email='admin@testcomplete.com'
        )
        
        # Crear técnico
        tecnico = TestDataFactory.create_test_user(
            username='tecnico_test_complete',
            password='tecnico123',
            first_name='Carlos',
            last_name='Técnico'
        )
        
        # Crear 3 proveedores con diferentes estados
        proveedores_data = []
        
        # Proveedor 1: Con plan aprobado
        user1, proveedor1 = TestDataFactory.create_test_proveedor()
        eval1 = TestDataFactory.create_test_evaluacion(proveedor1, puntaje=65)
        plan1 = TestDataFactory.create_test_plan(eval1, estado='APROBADO')
        plan1.revisado_por = tecnico
        plan1.fecha_revision = timezone.now()
        plan1.fecha_aprobacion = timezone.now()
        plan1.save()
        proveedores_data.append({
            'user': user1,
            'proveedor': proveedor1,
            'evaluacion': eval1,
            'plan': plan1
        })
        
        # Proveedor 2: Con plan en revisión
        user2, proveedor2 = TestDataFactory.create_test_proveedor()
        eval2 = TestDataFactory.create_test_evaluacion(proveedor2, puntaje=70)
        plan2 = TestDataFactory.create_test_plan(eval2, estado='EN_REVISION')
        proveedores_data.append({
            'user': user2,
            'proveedor': proveedor2,
            'evaluacion': eval2,
            'plan': plan2
        })
        
        # Proveedor 3: Sin plan (puntaje alto)
        user3, proveedor3 = TestDataFactory.create_test_proveedor()
        eval3 = TestDataFactory.create_test_evaluacion(proveedor3, puntaje=85)
        proveedores_data.append({
            'user': user3,
            'proveedor': proveedor3,
            'evaluacion': eval3,
            'plan': None
        })
        
        return {
            'admin': admin,
            'tecnico': tecnico,
            'proveedores': proveedores_data
        }


class URLTestHelper:
    """Ayudante para testing de URLs"""
    
    @staticmethod
    def get_test_urls() -> Dict[str, Dict]:
        """Retorna un diccionario con todas las URLs a probar y su configuración"""
        return {
            # URLs públicas
            'login': {
                'url': '/',
                'requires_auth': False,
                'expected_status': 200,
                'expected_content': ['Sistema de Planes', 'Iniciar Sesión']
            },
            
            # URLs de proveedor
            'dashboard': {
                'url': '/dashboard/',
                'requires_auth': True,
                'auth_user': 'proveedor',
                'expected_status': 200,
                'expected_content': ['Dashboard', 'Evaluación']
            },
            'crear_plan': {
                'url': '/crear-plan/{evaluacion_id}/',
                'requires_auth': True,
                'auth_user': 'proveedor',
                'requires_params': True,
                'expected_status': 200,
                'expected_content': ['Crear Plan', 'Análisis']
            },
            'ver_plan': {
                'url': '/ver-plan/{plan_id}/',
                'requires_auth': True,
                'auth_user': 'proveedor',
                'requires_params': True,
                'expected_status': 200,
                'expected_content': ['Plan de Mejoramiento']
            },
            'editar_plan': {
                'url': '/editar-plan/{plan_id}/',
                'requires_auth': True,
                'auth_user': 'proveedor',
                'requires_params': True,
                'expected_status': 200,
                'expected_content': ['Editar Plan']
            },
            
            # URLs de técnico
            'panel_tecnico': {
                'url': '/panel-tecnico/',
                'requires_auth': True,
                'auth_user': 'tecnico',
                'expected_status': 200,
                'expected_content': ['Panel de Control', 'Planes Pendientes']
            },
            'revisar_plan': {
                'url': '/revisar-plan/{plan_id}/',
                'requires_auth': True,
                'auth_user': 'tecnico',
                'requires_params': True,
                'expected_status': 200,
                'expected_content': ['Revisar Plan', 'Decisión']
            },
            'lista_proveedores': {
                'url': '/lista-proveedores/',
                'requires_auth': True,
                'auth_user': 'tecnico',
                'expected_status': 200,
                'expected_content': ['Lista de Proveedores']
            },
            
            # URLs de admin
            'admin': {
                'url': '/admin/',
                'requires_auth': True,
                'auth_user': 'admin',
                'expected_status': [200, 302],
                'expected_content': []
            },
            
            # URL de logout
            'logout': {
                'url': '/logout/',
                'requires_auth': False,
                'expected_status': 302,
                'expected_content': []
            }
        }
        
    @staticmethod
    def test_url_response(client: Client, url: str, expected_status: int = 200) -> bool:
        """Prueba que una URL responda con el status esperado"""
        response = client.get(url, follow=False)
        
        if isinstance(expected_status, list):
            return response.status_code in expected_status
        else:
            return response.status_code == expected_status
            
    @staticmethod
    def test_url_content(client: Client, url: str, expected_content: list) -> bool:
        """Prueba que una URL contenga el contenido esperado"""
        response = client.get(url)
        
        for content in expected_content:
            if content not in response.content.decode():
                return False
                
        return True
        
    @staticmethod
    def test_url_requires_auth(client: Client, url: str) -> bool:
        """Prueba que una URL requiera autenticación"""
        response = client.get(url, follow=False)
        return response.status_code in [302, 403]


class TestReporter:
    """Generador de reportes para tests"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def start(self):
        """Inicia el cronómetro del reporte"""
        self.start_time = timezone.now()
        
    def end(self):
        """Finaliza el cronómetro del reporte"""
        self.end_time = timezone.now()
        
    def add_result(self, test_name: str, status: str, message: str = "", time: float = 0):
        """Agrega un resultado al reporte"""
        self.results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'time': time
        })
        
    def generate_summary(self) -> Dict:
        """Genera un resumen del reporte"""
        total = len(self.results)
        success = len([r for r in self.results if r['status'] == 'SUCCESS'])
        warning = len([r for r in self.results if r['status'] == 'WARNING'])
        error = len([r for r in self.results if r['status'] == 'ERROR'])
        
        if self.start_time and self.end_time:
            total_time = (self.end_time - self.start_time).total_seconds()
        else:
            total_time = sum(r['time'] for r in self.results)
            
        return {
            'total': total,
            'success': success,
            'warning': warning,
            'error': error,
            'success_rate': (success / total * 100) if total > 0 else 0,
            'total_time': total_time
        }
        
    def print_report(self):
        """Imprime el reporte en consola"""
        summary = self.generate_summary()
        
        print("\n" + "="*60)
        print("📊 REPORTE DE TESTING")
        print("="*60)
        
        # Resultados individuales
        for result in self.results:
            icon = "✅" if result['status'] == 'SUCCESS' else "⚠️" if result['status'] == 'WARNING' else "❌"
            print(f"{icon} {result['test']}: {result['status']}")
            if result['message']:
                print(f"   {result['message']}")
                
        # Resumen
        print("\n" + "-"*60)
        print("RESUMEN:")
        print(f"  Total tests: {summary['total']}")
        print(f"  ✅ Exitosos: {summary['success']} ({summary['success']/summary['total']*100:.1f}%)")
        print(f"  ⚠️  Warnings: {summary['warning']} ({summary['warning']/summary['total']*100:.1f}%)")
        print(f"  ❌ Errores: {summary['error']} ({summary['error']/summary['total']*100:.1f}%)")
        print(f"  ⏱️  Tiempo total: {summary['total_time']:.2f} segundos")
        print(f"  🎯 Tasa de éxito: {summary['success_rate']:.1f}%")
        print("="*60)
        
    def export_html(self, filename: str):
        """Exporta el reporte a HTML"""
        summary = self.generate_summary()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reporte de Testing</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
                th {{ background: #333; color: white; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Reporte de Testing Automatizado</h1>
            <div class="summary">
                <h2>Resumen</h2>
                <p>Total de tests: {summary['total']}</p>
                <p class="success">Exitosos: {summary['success']} ({summary['success']/summary['total']*100:.1f}%)</p>
                <p class="warning">Warnings: {summary['warning']} ({summary['warning']/summary['total']*100:.1f}%)</p>
                <p class="error">Errores: {summary['error']} ({summary['error']/summary['total']*100:.1f}%)</p>
                <p>Tiempo total: {summary['total_time']:.2f} segundos</p>
                <p><strong>Tasa de éxito: {summary['success_rate']:.1f}%</strong></p>
            </div>
            
            <h2>Resultados Detallados</h2>
            <table>
                <tr>
                    <th>Test</th>
                    <th>Estado</th>
                    <th>Mensaje</th>
                    <th>Tiempo (s)</th>
                </tr>
        """
        
        for result in self.results:
            status_class = result['status'].lower()
            html += f"""
                <tr class="{status_class}">
                    <td>{result['test']}</td>
                    <td>{result['status']}</td>
                    <td>{result['message']}</td>
                    <td>{result['time']:.2f}</td>
                </tr>
            """
            
        html += """
            </table>
        </body>
        </html>
        """
        
        with open(filename, 'w') as f:
            f.write(html)
            
        print(f"📄 Reporte HTML exportado a: {filename}")