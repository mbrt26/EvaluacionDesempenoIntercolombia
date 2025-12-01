"""
Management Command para Testing Automatizado de Vistas
Ejecuta pruebas automáticas en todas las vistas del proyecto

Uso:
    python manage.py test_all_views
    python manage.py test_all_views --verbose
    python manage.py test_all_views --auth --create-user
    python manage.py test_all_views --export report.txt
"""

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.contrib.auth.models import User
from django.urls import get_resolver, reverse, NoReverseMatch
from django.db import transaction
from django.conf import settings
from planes.models import Proveedor, Evaluacion, PlanMejoramiento
from datetime import date, datetime, timedelta
import time
import sys
import re
from typing import Dict, List, Tuple, Optional


class Command(BaseCommand):
    help = 'Prueba automáticamente todas las vistas del proyecto Django'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Client()
        self.results = {
            'success': [],
            'warning': [],
            'error': [],
            'skipped': []
        }
        self.total_time = 0
        self.test_user = None
        self.test_proveedor = None
        self.test_tecnico = None
        
    def add_arguments(self, parser):
        """Define los argumentos del comando"""
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada de cada prueba'
        )
        
        parser.add_argument(
            '--auth',
            action='store_true',
            help='Prueba también las URLs que requieren autenticación'
        )
        
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Crea usuarios de prueba automáticamente'
        )
        
        parser.add_argument(
            '--export',
            type=str,
            help='Exporta el reporte a un archivo'
        )
        
        parser.add_argument(
            '--only-public',
            action='store_true',
            help='Prueba solo las URLs públicas'
        )
        
        parser.add_argument(
            '--only-auth',
            action='store_true',
            help='Prueba solo las URLs que requieren autenticación'
        )
        
        parser.add_argument(
            '--timeout',
            type=int,
            default=5,
            help='Timeout en segundos para cada request (default: 5)'
        )
        
    def handle(self, *args, **options):
        """Método principal del comando"""
        self.verbose = options['verbose']
        self.test_auth = options['auth']
        self.create_user = options['create_user']
        self.export_file = options.get('export')
        self.only_public = options['only_public']
        self.only_auth = options['only_auth']
        self.timeout = options['timeout']
        
        # Banner inicial
        self.print_banner()
        
        try:
            # Preparar datos de prueba si es necesario
            if self.create_user or self.test_auth:
                self.setup_test_data()
                
            # Descubrir todas las URLs
            self.stdout.write("🎯 Descubriendo URLs del proyecto...")
            urls = self.discover_urls()
            self.stdout.write(f"📊 Encontradas {len(urls)} URLs para probar\n")
            
            # Ejecutar pruebas
            self.stdout.write("🧪 Iniciando pruebas automatizadas...\n")
            start_time = time.time()
            
            for url_info in urls:
                self.test_url(url_info)
                
            self.total_time = time.time() - start_time
            
            # Mostrar resumen
            self.print_summary()
            
            # Exportar si se solicita
            if self.export_file:
                self.export_report()
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n\n⚠️  Pruebas interrumpidas por el usuario'))
            self.print_summary()
            
        except Exception as e:
            raise CommandError(f'Error durante las pruebas: {str(e)}')
            
    def print_banner(self):
        """Imprime el banner inicial"""
        banner = """
╔════════════════════════════════════════════════════════════╗
║          🧪 SISTEMA DE TESTING AUTOMATIZADO 🧪             ║
║           Planes de Mejoramiento - Intercolombia           ║
╚════════════════════════════════════════════════════════════╝
        """
        self.stdout.write(self.style.SUCCESS(banner))
        
    def setup_test_data(self):
        """Crea datos de prueba necesarios"""
        self.stdout.write("📦 Creando datos de prueba...")
        
        with transaction.atomic():
            # Crear o obtener usuario admin
            self.test_user, created = User.objects.get_or_create(
                username='test_admin_cmd',
                defaults={
                    'email': 'admin@testcmd.com',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                self.test_user.set_password('test123')
                self.test_user.save()
                
            # Crear usuario técnico
            self.test_tecnico, created = User.objects.get_or_create(
                username='test_tecnico_cmd',
                defaults={
                    'email': 'tecnico@testcmd.com',
                    'first_name': 'Técnico',
                    'last_name': 'Test'
                }
            )
            if created:
                self.test_tecnico.set_password('test123')
                self.test_tecnico.save()
                
            # Crear usuario proveedor
            self.test_proveedor, created = User.objects.get_or_create(
                username='900888888',
                defaults={'email': 'proveedor@testcmd.com'}
            )
            if created:
                self.test_proveedor.set_password('test123')
                self.test_proveedor.save()
                
            # Crear proveedor si no existe
            proveedor, created = Proveedor.objects.get_or_create(
                user=self.test_proveedor,
                defaults={
                    'nit': '900.888.888-8',
                    'razon_social': 'Empresa Test CMD',
                    'email': 'empresa@testcmd.com',
                    'telefono': '3008888888'
                }
            )
            
            # Crear evaluación si no existe
            evaluacion, created = Evaluacion.objects.get_or_create(
                proveedor=proveedor,
                periodo='2024-TEST',
                defaults={
                    'puntaje': 75,
                    'fecha': date.today(),
                    'puntaje_calidad': 80,
                    'puntaje_entrega': 70,
                    'puntaje_documentacion': 75,
                    'puntaje_precio': 75
                }
            )
            
        self.stdout.write(self.style.SUCCESS("   ✅ Datos de prueba creados\n"))
        
    def discover_urls(self) -> List[Dict]:
        """Descubre todas las URLs del proyecto"""
        urls = []
        resolver = get_resolver()
        
        def extract_urls(resolver, namespace=None, prefix=''):
            """Extrae URLs recursivamente"""
            for pattern in resolver.url_patterns:
                if hasattr(pattern, 'url_patterns'):
                    # Es un include
                    new_namespace = pattern.namespace or namespace
                    new_prefix = prefix + str(pattern.pattern)
                    extract_urls(pattern, new_namespace, new_prefix)
                else:
                    # Es una URL final
                    url_info = {
                        'pattern': str(pattern.pattern),
                        'name': pattern.name,
                        'namespace': namespace,
                        'full_name': f"{namespace}:{pattern.name}" if namespace and pattern.name else pattern.name,
                        'requires_params': self._requires_params(str(pattern.pattern)),
                        'is_admin': 'admin' in str(pattern.pattern),
                        'requires_auth': self._requires_auth(pattern.name or str(pattern.pattern))
                    }
                    
                    # Filtrar según opciones
                    if self.only_public and url_info['requires_auth']:
                        continue
                    if self.only_auth and not url_info['requires_auth']:
                        continue
                        
                    urls.append(url_info)
                    
        extract_urls(resolver)
        return urls
        
    def _requires_params(self, pattern: str) -> bool:
        """Determina si una URL requiere parámetros"""
        return '<' in pattern or '(?P' in pattern
        
    def _requires_auth(self, pattern_name: str) -> bool:
        """Determina si una URL probablemente requiere autenticación"""
        auth_patterns = [
            'dashboard', 'panel', 'crear', 'editar', 'revisar',
            'admin', 'logout', 'profile', 'settings'
        ]
        return any(word in pattern_name.lower() for word in auth_patterns)
        
    def test_url(self, url_info: Dict):
        """Prueba una URL específica"""
        # Saltar URLs con parámetros por ahora
        if url_info['requires_params']:
            if self.verbose:
                self.stdout.write(f"⏭️  {url_info['full_name'] or url_info['pattern']} -> SALTADA (requiere parámetros)")
            self.results['skipped'].append(url_info)
            return
            
        # Saltar URLs de admin si no estamos autenticados
        if url_info['is_admin'] and not self.test_auth:
            if self.verbose:
                self.stdout.write(f"⏭️  {url_info['pattern']} -> SALTADA (admin)")
            self.results['skipped'].append(url_info)
            return
            
        try:
            # Construir URL
            if url_info['full_name']:
                try:
                    url = reverse(url_info['full_name'])
                except NoReverseMatch:
                    url = self._build_url_from_pattern(url_info['pattern'])
            else:
                url = self._build_url_from_pattern(url_info['pattern'])
                
            # Login si es necesario
            if url_info['requires_auth'] and self.test_auth:
                if 'tecnico' in url_info['pattern'] or 'panel' in url_info['pattern']:
                    self.client.login(username='test_tecnico_cmd', password='test123')
                elif 'admin' in url_info['pattern']:
                    self.client.login(username='test_admin_cmd', password='test123')
                else:
                    self.client.login(username='900888888', password='test123')
                    
            # Hacer request con timeout
            start = time.time()
            response = self.client.get(url, follow=False)
            elapsed = time.time() - start
            
            # Evaluar resultado
            status = response.status_code
            
            if status == 200:
                self._log_success(url, status, elapsed)
                self.results['success'].append({'url': url, 'status': status, 'time': elapsed})
                
            elif 300 <= status < 400:
                self._log_warning(url, status, "Redirect")
                self.results['warning'].append({'url': url, 'status': status, 'reason': 'Redirect'})
                
            elif status == 403:
                if url_info['requires_auth']:
                    self._log_warning(url, status, "Forbidden (esperado)")
                    self.results['warning'].append({'url': url, 'status': status, 'reason': 'Forbidden'})
                else:
                    self._log_error(url, status)
                    self.results['error'].append({'url': url, 'status': status})
                    
            elif status == 404:
                self._log_error(url, status)
                self.results['error'].append({'url': url, 'status': status})
                
            elif status >= 500:
                self._log_error(url, status)
                self.results['error'].append({'url': url, 'status': status})
                
            else:
                self._log_warning(url, status, "Status inesperado")
                self.results['warning'].append({'url': url, 'status': status, 'reason': 'Unexpected'})
                
            # Logout después de cada prueba
            if url_info['requires_auth']:
                self.client.logout()
                
        except Exception as e:
            self._log_error(url_info['pattern'], 'ERROR', str(e))
            self.results['error'].append({'url': url_info['pattern'], 'error': str(e)})
            
    def _build_url_from_pattern(self, pattern: str) -> str:
        """Construye una URL desde un patrón"""
        # Limpiar el patrón
        url = pattern
        if url.startswith('^'):
            url = url[1:]
        if url.endswith('$'):
            url = url[:-1]
            
        # Agregar / al inicio si no lo tiene
        if not url.startswith('/'):
            url = '/' + url
            
        return url
        
    def _log_success(self, url: str, status: int, elapsed: float):
        """Registra un éxito"""
        if self.verbose:
            self.stdout.write(
                self.style.SUCCESS(f"✅ {url} -> {status} OK ({elapsed:.2f}s)")
            )
            
    def _log_warning(self, url: str, status: int, reason: str = ""):
        """Registra una advertencia"""
        if self.verbose:
            msg = f"⚠️  {url} -> {status}"
            if reason:
                msg += f" ({reason})"
            self.stdout.write(self.style.WARNING(msg))
            
    def _log_error(self, url: str, status, error: str = ""):
        """Registra un error"""
        msg = f"❌ {url} -> {status}"
        if error:
            msg += f" ({error})"
        self.stdout.write(self.style.ERROR(msg))
        
    def print_summary(self):
        """Imprime el resumen de resultados"""
        total_tested = len(self.results['success']) + len(self.results['warning']) + len(self.results['error'])
        total_urls = total_tested + len(self.results['skipped'])
        
        # Calcular porcentajes
        if total_tested > 0:
            success_rate = (len(self.results['success']) / total_tested) * 100
            warning_rate = (len(self.results['warning']) / total_tested) * 100
            error_rate = (len(self.results['error']) / total_tested) * 100
        else:
            success_rate = warning_rate = error_rate = 0
            
        # Imprimir resumen
        summary = f"""
{'='*60}
📈 RESUMEN FINAL:
   Total URLs encontradas: {total_urls}
   Total URLs probadas: {total_tested}
   ⏭️  URLs saltadas: {len(self.results['skipped'])}
   
   ✅ Exitosas: {len(self.results['success'])} ({success_rate:.1f}%)
   ⚠️  Con advertencias: {len(self.results['warning'])} ({warning_rate:.1f}%)
   ❌ Con errores: {len(self.results['error'])} ({error_rate:.1f}%)
   
🎯 Tasa de éxito general: {success_rate:.1f}%
⏱️  Tiempo total: {self.total_time:.2f} segundos
{'='*60}
        """
        
        if success_rate >= 90:
            self.stdout.write(self.style.SUCCESS(summary))
        elif success_rate >= 70:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.ERROR(summary))
            
        # Mostrar URLs con errores si hay
        if self.results['error'] and self.verbose:
            self.stdout.write("\n❌ URLs con errores:")
            for item in self.results['error']:
                self.stdout.write(f"   - {item.get('url', item.get('pattern', 'Unknown'))}")
                
    def export_report(self):
        """Exporta el reporte a un archivo"""
        try:
            with open(self.export_file, 'w') as f:
                f.write("="*60 + "\n")
                f.write("REPORTE DE TESTING AUTOMATIZADO\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n\n")
                
                # URLs exitosas
                f.write("URLS EXITOSAS:\n")
                for item in self.results['success']:
                    f.write(f"  ✅ {item['url']} -> {item['status']} ({item['time']:.2f}s)\n")
                    
                f.write("\n")
                
                # URLs con advertencias
                f.write("URLS CON ADVERTENCIAS:\n")
                for item in self.results['warning']:
                    f.write(f"  ⚠️  {item['url']} -> {item['status']} ({item.get('reason', '')})\n")
                    
                f.write("\n")
                
                # URLs con errores
                f.write("URLS CON ERRORES:\n")
                for item in self.results['error']:
                    f.write(f"  ❌ {item.get('url', 'Unknown')} -> {item.get('status', item.get('error', 'ERROR'))}\n")
                    
                f.write("\n")
                
                # URLs saltadas
                f.write("URLS SALTADAS:\n")
                for item in self.results['skipped']:
                    f.write(f"  ⏭️  {item.get('full_name', item.get('pattern', 'Unknown'))}\n")
                    
                f.write("\n" + "="*60 + "\n")
                
                # Resumen
                total_tested = len(self.results['success']) + len(self.results['warning']) + len(self.results['error'])
                if total_tested > 0:
                    success_rate = (len(self.results['success']) / total_tested) * 100
                else:
                    success_rate = 0
                    
                f.write("RESUMEN:\n")
                f.write(f"  Total URLs probadas: {total_tested}\n")
                f.write(f"  Exitosas: {len(self.results['success'])}\n")
                f.write(f"  Con advertencias: {len(self.results['warning'])}\n")
                f.write(f"  Con errores: {len(self.results['error'])}\n")
                f.write(f"  Saltadas: {len(self.results['skipped'])}\n")
                f.write(f"  Tasa de éxito: {success_rate:.1f}%\n")
                f.write(f"  Tiempo total: {self.total_time:.2f} segundos\n")
                
            self.stdout.write(self.style.SUCCESS(f"\n📄 Reporte exportado a: {self.export_file}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error al exportar reporte: {str(e)}"))