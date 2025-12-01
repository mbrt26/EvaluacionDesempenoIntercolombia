#!/usr/bin/env python
"""
Script ejecutable independiente para testing automatizado de vistas
Puede ejecutarse directamente sin usar manage.py

Uso:
    python scripts/run_view_tests.py
    python scripts/run_view_tests.py --full
    python scripts/run_view_tests.py --quick
    python scripts/run_view_tests.py --report
"""

import os
import sys
import django
from pathlib import Path

# Configurar el path del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Ahora importar las dependencias de Django
from django.test import Client
from django.contrib.auth.models import User
from planes.utils.testing_utils import TestDataFactory, URLTestHelper, TestReporter
from planes.models import Proveedor, Evaluacion, PlanMejoramiento
import argparse
import time
from datetime import datetime


class ViewTestRunner:
    """Ejecutor principal de tests de vistas"""
    
    def __init__(self, mode='standard'):
        self.mode = mode
        self.client = Client()
        self.reporter = TestReporter()
        self.test_data = {}
        
    def setup(self):
        """Configura los datos de prueba"""
        print("🔧 Configurando entorno de pruebas...")
        
        # Limpiar datos antiguos de prueba
        User.objects.filter(username__startswith='test_script_').delete()
        
        # Crear datos de prueba
        self.test_data = TestDataFactory.create_complete_test_scenario()
        
        print("✅ Entorno configurado\n")
        
    def teardown(self):
        """Limpia los datos de prueba"""
        print("\n🧹 Limpiando datos de prueba...")
        
        # Eliminar usuarios de prueba
        User.objects.filter(username__contains='test_').delete()
        
        print("✅ Limpieza completada")
        
    def run_quick_tests(self):
        """Ejecuta tests rápidos (solo URLs públicas)"""
        print("⚡ MODO RÁPIDO - Testing de URLs públicas\n")
        
        self.reporter.start()
        
        # Test de login
        print("📍 Testing vista de login...")
        response = self.client.get('/')
        if response.status_code == 200:
            self.reporter.add_result('Login View', 'SUCCESS', 'Vista carga correctamente')
            print("   ✅ Login page: OK")
        else:
            self.reporter.add_result('Login View', 'ERROR', f'Status: {response.status_code}')
            print(f"   ❌ Login page: {response.status_code}")
            
        # Test de login POST
        print("📍 Testing autenticación...")
        proveedor_data = self.test_data['proveedores'][0]
        response = self.client.post('/', {
            'username': proveedor_data['user'].username,
            'password': 'proveedor123'
        })
        if response.status_code == 302:
            self.reporter.add_result('Login POST', 'SUCCESS', 'Autenticación funciona')
            print("   ✅ Autenticación: OK")
        else:
            self.reporter.add_result('Login POST', 'ERROR', 'Autenticación falla')
            print("   ❌ Autenticación: ERROR")
            
        # Test de logout
        print("📍 Testing logout...")
        response = self.client.get('/logout/', follow=False)
        if response.status_code == 302:
            self.reporter.add_result('Logout', 'SUCCESS', 'Logout funciona')
            print("   ✅ Logout: OK")
        else:
            self.reporter.add_result('Logout', 'ERROR', f'Status: {response.status_code}')
            print(f"   ❌ Logout: {response.status_code}")
            
        self.reporter.end()
        
    def run_standard_tests(self):
        """Ejecuta tests estándar (públicas + autenticadas básicas)"""
        print("📋 MODO ESTÁNDAR - Testing de vistas principales\n")
        
        self.reporter.start()
        
        # Tests públicos
        self.run_quick_tests()
        
        # Tests de proveedor
        print("\n🔐 Testing vistas de proveedor...")
        proveedor_data = self.test_data['proveedores'][0]
        self.client.login(
            username=proveedor_data['user'].username,
            password='proveedor123'
        )
        
        # Dashboard
        print("📍 Testing dashboard proveedor...")
        response = self.client.get('/dashboard/')
        if response.status_code == 200:
            self.reporter.add_result('Dashboard Proveedor', 'SUCCESS')
            print("   ✅ Dashboard: OK")
        else:
            self.reporter.add_result('Dashboard Proveedor', 'ERROR', f'Status: {response.status_code}')
            print(f"   ❌ Dashboard: {response.status_code}")
            
        # Ver plan
        if proveedor_data['plan']:
            print("📍 Testing ver plan...")
            response = self.client.get(f"/ver-plan/{proveedor_data['plan'].id}/")
            if response.status_code == 200:
                self.reporter.add_result('Ver Plan', 'SUCCESS')
                print("   ✅ Ver plan: OK")
            else:
                self.reporter.add_result('Ver Plan', 'ERROR', f'Status: {response.status_code}')
                print(f"   ❌ Ver plan: {response.status_code}")
                
        self.client.logout()
        
        # Tests de técnico
        print("\n👨‍💼 Testing vistas de técnico...")
        self.client.login(
            username=self.test_data['tecnico'].username,
            password='tecnico123'
        )
        
        # Panel técnico
        print("📍 Testing panel técnico...")
        response = self.client.get('/panel-tecnico/')
        if response.status_code == 200:
            self.reporter.add_result('Panel Técnico', 'SUCCESS')
            print("   ✅ Panel técnico: OK")
        else:
            self.reporter.add_result('Panel Técnico', 'ERROR', f'Status: {response.status_code}')
            print(f"   ❌ Panel técnico: {response.status_code}")
            
        # Lista proveedores
        print("📍 Testing lista proveedores...")
        response = self.client.get('/lista-proveedores/')
        if response.status_code == 200:
            self.reporter.add_result('Lista Proveedores', 'SUCCESS')
            print("   ✅ Lista proveedores: OK")
        else:
            self.reporter.add_result('Lista Proveedores', 'ERROR', f'Status: {response.status_code}')
            print(f"   ❌ Lista proveedores: {response.status_code}")
            
        self.client.logout()
        self.reporter.end()
        
    def run_full_tests(self):
        """Ejecuta todos los tests disponibles"""
        print("🔥 MODO COMPLETO - Testing exhaustivo de todas las vistas\n")
        
        self.reporter.start()
        
        # Ejecutar tests estándar primero
        self.run_standard_tests()
        
        # Tests adicionales de admin
        print("\n🛡️ Testing panel de administración...")
        self.client.login(
            username=self.test_data['admin'].username,
            password='admin123'
        )
        
        admin_urls = [
            '/admin/',
            '/admin/auth/',
            '/admin/planes/',
        ]
        
        for url in admin_urls:
            response = self.client.get(url)
            if response.status_code in [200, 301, 302]:
                self.reporter.add_result(f'Admin: {url}', 'SUCCESS')
                print(f"   ✅ {url}: OK")
            else:
                self.reporter.add_result(f'Admin: {url}', 'ERROR', f'Status: {response.status_code}')
                print(f"   ❌ {url}: {response.status_code}")
                
        self.client.logout()
        
        # Tests de seguridad
        print("\n🔒 Testing seguridad...")
        
        # Intentar acceder sin autenticación
        print("📍 Testing control de acceso...")
        protected_urls = [
            '/dashboard/',
            '/panel-tecnico/',
            '/lista-proveedores/'
        ]
        
        for url in protected_urls:
            response = self.client.get(url, follow=False)
            if response.status_code in [302, 403]:
                self.reporter.add_result(f'Seguridad: {url}', 'SUCCESS', 'Protegido correctamente')
                print(f"   ✅ {url}: Protegido")
            else:
                self.reporter.add_result(f'Seguridad: {url}', 'ERROR', 'No está protegido')
                print(f"   ❌ {url}: NO protegido")
                
        self.reporter.end()
        
    def generate_report(self):
        """Genera y muestra el reporte final"""
        print("\n" + "="*60)
        self.reporter.print_report()
        
        # Guardar reporte HTML si se solicita
        if '--html' in sys.argv:
            filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            self.reporter.export_html(filename)
            
    def run(self):
        """Ejecuta el proceso completo de testing"""
        try:
            self.setup()
            
            if self.mode == 'quick':
                self.run_quick_tests()
            elif self.mode == 'full':
                self.run_full_tests()
            else:
                self.run_standard_tests()
                
            self.generate_report()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Testing interrumpido por el usuario")
            
        except Exception as e:
            print(f"\n❌ Error durante el testing: {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.teardown()


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description='Testing automatizado de vistas Django'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Ejecuta solo tests rápidos (URLs públicas)'
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Ejecuta todos los tests disponibles'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Genera reporte detallado'
    )
    
    parser.add_argument(
        '--html',
        action='store_true',
        help='Exporta reporte en formato HTML'
    )
    
    args = parser.parse_args()
    
    # Determinar modo
    if args.quick:
        mode = 'quick'
    elif args.full:
        mode = 'full'
    else:
        mode = 'standard'
        
    # Banner
    print("""
╔════════════════════════════════════════════════════════════╗
║              🧪 TESTING AUTOMATIZADO DE VISTAS 🧪           ║
║                    Sistema de Planes de Mejoramiento        ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Modo: {mode.upper()}")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60 + "\n")
    
    # Ejecutar tests
    runner = ViewTestRunner(mode=mode)
    runner.run()
    
    print("\n✨ Testing completado")


if __name__ == '__main__':
    main()