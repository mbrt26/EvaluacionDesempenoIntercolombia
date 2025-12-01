"""
Sistema de Descubrimiento Automático de URLs y Vistas
Encuentra y categoriza todas las URLs del proyecto Django
"""

import re
from django.test import TestCase, Client
from django.urls import get_resolver, reverse, NoReverseMatch
from django.contrib.auth.models import User
from django.conf import settings
from typing import List, Dict, Tuple, Optional
import inspect


class URLPattern:
    """Clase para representar un patrón de URL con sus metadatos"""
    
    def __init__(self, pattern, name=None, namespace=None):
        self.pattern = pattern
        self.name = name
        self.namespace = namespace
        self.full_name = f"{namespace}:{name}" if namespace else name
        self.requires_auth = False
        self.requires_params = False
        self.param_types = {}
        self.view_class = None
        self.view_function = None
        
    def __str__(self):
        return f"URL({self.full_name or self.pattern})"
    
    def __repr__(self):
        return f"<URLPattern: {self.full_name or self.pattern}>"


class ViewsDiscoveryTest(TestCase):
    """
    Clase principal para descubrimiento y testing automático de vistas
    """
    
    @classmethod
    def setUpTestData(cls):
        """Crear datos de prueba una sola vez para toda la clase"""
        # Crear usuarios de prueba
        cls.admin_user = User.objects.create_superuser(
            username='test_admin',
            password='test_admin123',
            email='admin@test.com'
        )
        
        cls.normal_user = User.objects.create_user(
            username='test_user',
            password='test_user123',
            email='user@test.com'
        )
        
        cls.tecnico_user = User.objects.create_user(
            username='test_tecnico',
            password='test_tecnico123',
            email='tecnico@test.com',
            first_name='Técnico',
            last_name='Prueba'
        )
        
        cls.proveedor_user = User.objects.create_user(
            username='900999999',
            password='test_proveedor123',
            email='proveedor@test.com'
        )
        
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        self.discovered_urls = []
        self.categorized_urls = {
            'public': [],
            'authenticated': [],
            'admin': [],
            'api': [],
            'with_params': [],
            'static': []
        }
        
    def test_discover_all_urls(self):
        """Test principal: descubre todas las URLs del proyecto"""
        print("\n" + "="*60)
        print("🎯 DESCUBRIMIENTO AUTOMÁTICO DE URLs")
        print("="*60)
        
        # Obtener todas las URLs
        self.discovered_urls = self._discover_project_urls()
        
        # Categorizar URLs
        self._categorize_urls()
        
        # Mostrar resumen
        self._print_discovery_summary()
        
        # Verificar que se encontraron URLs
        self.assertGreater(len(self.discovered_urls), 0, 
                          "No se encontraron URLs en el proyecto")
        
    def test_public_urls(self):
        """Prueba todas las URLs públicas (sin autenticación)"""
        print("\n" + "="*60)
        print("🌍 TESTING DE URLs PÚBLICAS")
        print("="*60)
        
        # Descubrir y categorizar URLs
        self.discovered_urls = self._discover_project_urls()
        self._categorize_urls()
        
        public_urls = self.categorized_urls['public']
        results = {'success': 0, 'redirect': 0, 'error': 0}
        
        for url_pattern in public_urls:
            try:
                # Intentar obtener la URL
                url = self._get_url_path(url_pattern)
                if not url:
                    continue
                    
                response = self.client.get(url, follow=False)
                status = response.status_code
                
                if 200 <= status < 300:
                    print(f"✅ {url_pattern.full_name or url} -> {status}")
                    results['success'] += 1
                elif 300 <= status < 400:
                    print(f"⚠️  {url_pattern.full_name or url} -> {status} (Redirect)")
                    results['redirect'] += 1
                else:
                    print(f"❌ {url_pattern.full_name or url} -> {status}")
                    results['error'] += 1
                    
            except Exception as e:
                print(f"❌ {url_pattern.full_name} -> ERROR: {str(e)}")
                results['error'] += 1
                
        # Resumen
        total = sum(results.values())
        if total > 0:
            success_rate = (results['success'] / total) * 100
            print(f"\n📊 Resumen URLs Públicas:")
            print(f"   Total: {total}")
            print(f"   ✅ Exitosas: {results['success']} ({results['success']/total*100:.1f}%)")
            print(f"   ⚠️  Redirects: {results['redirect']} ({results['redirect']/total*100:.1f}%)")
            print(f"   ❌ Errores: {results['error']} ({results['error']/total*100:.1f}%)")
            
    def test_authenticated_urls(self):
        """Prueba todas las URLs que requieren autenticación"""
        print("\n" + "="*60)
        print("🔐 TESTING DE URLs CON AUTENTICACIÓN")
        print("="*60)
        
        # Descubrir y categorizar URLs
        self.discovered_urls = self._discover_project_urls()
        self._categorize_urls()
        
        auth_urls = self.categorized_urls['authenticated']
        
        # Probar sin autenticación (deben redirigir o dar 403)
        print("\n📍 Sin autenticación:")
        for url_pattern in auth_urls[:5]:  # Limitar a 5 para ejemplo
            try:
                url = self._get_url_path(url_pattern)
                if not url:
                    continue
                    
                response = self.client.get(url, follow=False)
                status = response.status_code
                
                if status in [302, 403]:
                    print(f"✅ {url} -> {status} (Protegido correctamente)")
                else:
                    print(f"⚠️  {url} -> {status} (Debería estar protegido)")
                    
            except Exception as e:
                print(f"❌ {url_pattern.full_name} -> ERROR: {str(e)}")
                
        # Probar con autenticación
        print("\n📍 Con autenticación:")
        self.client.login(username='test_user', password='test_user123')
        
        results = {'success': 0, 'forbidden': 0, 'error': 0}
        
        for url_pattern in auth_urls:
            try:
                url = self._get_url_path(url_pattern)
                if not url:
                    continue
                    
                response = self.client.get(url, follow=False)
                status = response.status_code
                
                if 200 <= status < 300:
                    print(f"✅ {url} -> {status}")
                    results['success'] += 1
                elif status == 403:
                    print(f"⚠️  {url} -> 403 (Permisos insuficientes)")
                    results['forbidden'] += 1
                elif 300 <= status < 400:
                    print(f"ℹ️  {url} -> {status} (Redirect)")
                    results['success'] += 1
                else:
                    print(f"❌ {url} -> {status}")
                    results['error'] += 1
                    
            except Exception as e:
                print(f"❌ {url_pattern.full_name} -> ERROR: {str(e)}")
                results['error'] += 1
                
        # Resumen
        total = sum(results.values())
        if total > 0:
            print(f"\n📊 Resumen URLs Autenticadas:")
            print(f"   Total: {total}")
            print(f"   ✅ Exitosas: {results['success']} ({results['success']/total*100:.1f}%)")
            print(f"   ⚠️  Sin permisos: {results['forbidden']} ({results['forbidden']/total*100:.1f}%)")
            print(f"   ❌ Errores: {results['error']} ({results['error']/total*100:.1f}%)")
            
    def test_admin_urls(self):
        """Prueba las URLs del admin de Django"""
        print("\n" + "="*60)
        print("🛡️ TESTING DE URLs DE ADMIN")
        print("="*60)
        
        # Login como admin
        self.client.login(username='test_admin', password='test_admin123')
        
        admin_urls = [
            '/admin/',
            '/admin/auth/user/',
            '/admin/auth/group/',
            '/admin/planes/proveedor/',
            '/admin/planes/evaluacion/',
            '/admin/planes/planmejoramiento/',
        ]
        
        for url in admin_urls:
            try:
                response = self.client.get(url)
                status = response.status_code
                
                if status == 200:
                    print(f"✅ {url} -> {status}")
                else:
                    print(f"❌ {url} -> {status}")
                    
            except Exception as e:
                print(f"❌ {url} -> ERROR: {str(e)}")
                
    # ===================== MÉTODOS AUXILIARES =====================
    
    def _discover_project_urls(self) -> List[URLPattern]:
        """
        Descubre todas las URLs del proyecto usando el resolver de Django
        """
        urls = []
        resolver = get_resolver()
        
        def extract_urls(resolver, namespace=None):
            """Función recursiva para extraer URLs"""
            for pattern in resolver.url_patterns:
                if hasattr(pattern, 'url_patterns'):
                    # Es un include, recursión
                    new_namespace = pattern.namespace or namespace
                    extract_urls(pattern, new_namespace)
                else:
                    # Es una URL final
                    url_obj = URLPattern(
                        pattern=str(pattern.pattern),
                        name=pattern.name,
                        namespace=namespace
                    )
                    
                    # Detectar si requiere parámetros
                    if '<' in str(pattern.pattern) or '(?P' in str(pattern.pattern):
                        url_obj.requires_params = True
                        url_obj.param_types = self._extract_params(str(pattern.pattern))
                        
                    # Obtener información de la vista
                    if hasattr(pattern, 'callback'):
                        url_obj.view_function = pattern.callback
                        
                    urls.append(url_obj)
                    
        extract_urls(resolver)
        return urls
        
    def _categorize_urls(self):
        """Categoriza las URLs descubiertas"""
        for url in self.discovered_urls:
            pattern_str = str(url.pattern)
            
            # URLs del admin
            if 'admin' in pattern_str:
                self.categorized_urls['admin'].append(url)
                
            # URLs de API
            elif 'api' in pattern_str:
                self.categorized_urls['api'].append(url)
                
            # URLs con parámetros
            elif url.requires_params:
                self.categorized_urls['with_params'].append(url)
                
            # URLs estáticas
            elif 'static' in pattern_str or 'media' in pattern_str:
                self.categorized_urls['static'].append(url)
                
            # URLs que probablemente requieren autenticación
            elif any(word in pattern_str for word in ['dashboard', 'panel', 'crear', 'editar', 'revisar']):
                self.categorized_urls['authenticated'].append(url)
                
            # URLs públicas
            else:
                self.categorized_urls['public'].append(url)
                
    def _extract_params(self, pattern: str) -> Dict[str, str]:
        """Extrae los parámetros y sus tipos de un patrón de URL"""
        params = {}
        
        # Buscar parámetros tipo <int:id>
        django_params = re.findall(r'<(\w+):(\w+)>', pattern)
        for param_type, param_name in django_params:
            params[param_name] = param_type
            
        # Buscar parámetros tipo (?P<id>\d+)
        regex_params = re.findall(r'\(\?P<(\w+)>([^)]+)\)', pattern)
        for param_name, param_pattern in regex_params:
            if '\\d' in param_pattern:
                params[param_name] = 'int'
            else:
                params[param_name] = 'str'
                
        return params
        
    def _get_url_path(self, url_pattern: URLPattern) -> Optional[str]:
        """Obtiene el path de una URL, generando parámetros si es necesario"""
        if not url_pattern.requires_params:
            # URL sin parámetros
            if url_pattern.full_name:
                try:
                    return reverse(url_pattern.full_name)
                except NoReverseMatch:
                    pass
                    
            # Intentar con el patrón directamente
            pattern = str(url_pattern.pattern)
            if pattern.startswith('^'):
                pattern = pattern[1:]
            if pattern.endswith('$'):
                pattern = pattern[:-1]
            return '/' + pattern if not pattern.startswith('/') else pattern
            
        else:
            # URL con parámetros - generar valores de prueba
            if url_pattern.full_name:
                kwargs = {}
                for param_name, param_type in url_pattern.param_types.items():
                    if param_type in ['int', 'pk', 'id']:
                        kwargs[param_name] = 1
                    elif param_type == 'slug':
                        kwargs[param_name] = 'test-slug'
                    else:
                        kwargs[param_name] = 'test'
                        
                try:
                    return reverse(url_pattern.full_name, kwargs=kwargs)
                except (NoReverseMatch, TypeError):
                    pass
                    
        return None
        
    def _print_discovery_summary(self):
        """Imprime un resumen del descubrimiento de URLs"""
        total = len(self.discovered_urls)
        
        print(f"\n📊 RESUMEN DE DESCUBRIMIENTO:")
        print(f"   Total URLs encontradas: {total}")
        print(f"\n📁 Categorías:")
        
        for category, urls in self.categorized_urls.items():
            if urls:
                print(f"   • {category.upper()}: {len(urls)} URLs")
                # Mostrar algunas URLs de ejemplo
                for url in urls[:3]:
                    print(f"     - {url.full_name or url.pattern}")
                if len(urls) > 3:
                    print(f"     ... y {len(urls) - 3} más")
                    
        print("\n" + "="*60)