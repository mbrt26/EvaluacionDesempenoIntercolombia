#!/usr/bin/env python
"""
Script para inicializar datos en producción
Ejecutar con: python manage.py shell < init_production_data.py
"""

from django.contrib.auth.models import User
from planes.models import Proveedor, PerfilUsuario

# Crear usuario gestor
try:
    gestor_user = User.objects.get(username='gestor1')
    gestor_user.set_password('Gestor123!@#')
    gestor_user.save()
    print("✓ Contraseña actualizada para gestor1")
except User.DoesNotExist:
    gestor_user = User.objects.create_user(
        username='gestor1',
        password='Gestor123!@#',
        email='gestor@intercolombia.com',
        first_name='Gestor',
        last_name='Planes'
    )
    print(f"✓ Usuario gestor creado: gestor1 / Gestor123!@#")

# Crear perfil de gestor si no existe
if not hasattr(gestor_user, 'perfil'):
    PerfilUsuario.objects.create(
        user=gestor_user,
        tipo_perfil='GESTOR',
        requiere_cambio_password=False
    )
    print("✓ Perfil GESTOR creado para gestor1")
else:
    gestor_user.perfil.tipo_perfil = 'GESTOR'
    gestor_user.perfil.requiere_cambio_password = False
    gestor_user.perfil.save()

# Crear usuario técnico
try:
    tecnico_user = User.objects.get(username='tecnico2')
    tecnico_user.set_password('Tecnico123!@#')
    tecnico_user.save()
    print("✓ Contraseña actualizada para tecnico2")
except User.DoesNotExist:
    tecnico_user = User.objects.create_user(
        username='tecnico2',
        password='Tecnico123!@#',
        email='tecnico2@intercolombia.com',
        first_name='Técnico',
        last_name='Evaluador'
    )
    print(f"✓ Usuario técnico creado: tecnico2 / Tecnico123!@#")

# Crear perfil de técnico si no existe
if not hasattr(tecnico_user, 'perfil'):
    PerfilUsuario.objects.create(
        user=tecnico_user,
        tipo_perfil='TECNICO',
        requiere_cambio_password=False
    )
    print("✓ Perfil TECNICO creado para tecnico2")
else:
    tecnico_user.perfil.tipo_perfil = 'TECNICO'
    tecnico_user.perfil.requiere_cambio_password = False
    tecnico_user.perfil.save()

# Crear usuario proveedor
try:
    prov_user = User.objects.get(username='900888777')
    prov_user.set_password('Proveedor123!@#')
    prov_user.save()
    print("✓ Contraseña actualizada para 900888777")
    
    # Verificar si ya tiene proveedor asociado
    if not hasattr(prov_user, 'proveedor'):
        proveedor = Proveedor.objects.create(
            user=prov_user,
            nit='900888777',
            razon_social='Empresa Test S.A.S',
            email='proveedor@test.com',
            email_adicional='gestor@test.com',
            activo=True
        )
        print(f"✓ Proveedor asociado al usuario 900888777")
    else:
        print("ℹ Usuario 900888777 ya tiene proveedor asociado")
        
except User.DoesNotExist:
    prov_user = User.objects.create_user(
        username='900888777',
        password='Proveedor123!@#',
        email='proveedor@test.com',
        first_name='Empresa',
        last_name='Test'
    )
    
    proveedor = Proveedor.objects.create(
        user=prov_user,
        nit='900888777',
        razon_social='Empresa Test S.A.S',
        email='proveedor@test.com',
        email_adicional='gestor@test.com',
        activo=True
    )
    print(f"✓ Proveedor creado: NIT 900888777 / contraseña: Proveedor123!@#")

# Crear perfil de proveedor si no existe
if not hasattr(prov_user, 'perfil'):
    PerfilUsuario.objects.create(
        user=prov_user,
        tipo_perfil='PROVEEDOR',
        requiere_cambio_password=True  # Debe cambiar en primer acceso
    )
    print("✓ Perfil PROVEEDOR creado para 900888777")
else:
    prov_user.perfil.tipo_perfil = 'PROVEEDOR'
    prov_user.perfil.save()

print("\n✅ Datos iniciales configurados correctamente")
print("\n=== CREDENCIALES DE ACCESO ===")
print("GESTOR: gestor1 / Gestor123!@#")
print("TÉCNICO: tecnico2 / Tecnico123!@#") 
print("PROVEEDOR: 900888777 / Proveedor123!@#")
print("\nNOTA: Los proveedores deben cambiar su contraseña en el primer acceso")