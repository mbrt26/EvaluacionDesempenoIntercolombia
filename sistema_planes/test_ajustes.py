#!/usr/bin/env python
"""
Script de prueba para verificar los ajustes implementados
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from planes.models import Proveedor, Evaluacion, PlanMejoramiento, HistorialEstado
from datetime import date, datetime


def test_campo_email_adicional():
    """Verificar que el modelo Proveedor tiene el campo email_adicional"""
    print("✓ Probando campo email_adicional en modelo Proveedor...")
    
    # Verificar que el campo existe
    field_names = [field.name for field in Proveedor._meta.get_fields()]
    
    if 'email_adicional' in field_names:
        print("  ✓ Campo email_adicional existe")
    else:
        print("  ✗ Campo email_adicional NO existe")
        return False
    
    if 'telefono' in field_names:
        print("  ✗ Campo telefono todavía existe (debería haberse eliminado)")
        return False
    else:
        print("  ✓ Campo telefono eliminado correctamente")
    
    # Verificar que el campo es opcional
    field = Proveedor._meta.get_field('email_adicional')
    if field.blank and field.null:
        print("  ✓ Campo email_adicional es opcional (blank=True, null=True)")
    else:
        print("  ✗ Campo email_adicional NO es opcional")
        return False
    
    return True


def test_estado_firmado_enviado():
    """Verificar que existe el estado FIRMADO_ENVIADO"""
    print("\n✓ Probando estado FIRMADO_ENVIADO en PlanMejoramiento...")
    
    estados_disponibles = dict(PlanMejoramiento.ESTADOS)
    
    if 'FIRMADO_ENVIADO' in estados_disponibles:
        print("  ✓ Estado FIRMADO_ENVIADO existe")
        print(f"    Descripción: {estados_disponibles['FIRMADO_ENVIADO']}")
    else:
        print("  ✗ Estado FIRMADO_ENVIADO NO existe")
        return False
    
    return True


def test_creacion_automatica_usuario():
    """Probar la creación automática de usuario al cambiar estado a FIRMADO_ENVIADO"""
    print("\n✓ Probando creación automática de usuario...")
    
    try:
        # Limpiar datos de prueba anteriores
        User.objects.filter(username='test999999999').delete()
        Proveedor.objects.filter(nit='test999999999').delete()
        
        # Crear un proveedor sin usuario
        proveedor_sin_usuario = Proveedor.objects.create(
            nit='test999999999',
            razon_social='Empresa de Prueba S.A.S',
            email='prueba@ejemplo.com',
            email_adicional='gestor@ejemplo.com',
            activo=True,
            user=None  # Sin usuario asociado inicialmente
        )
        print(f"  ✓ Proveedor de prueba creado: {proveedor_sin_usuario.razon_social}")
        
        # Crear una evaluación de prueba
        evaluacion = Evaluacion.objects.create(
            proveedor=proveedor_sin_usuario,
            periodo='2024-Q1',
            puntaje=65,  # Puntaje bajo para requerir plan
            fecha=date.today(),
            puntaje_calidad=15,
            puntaje_entrega=20,
            puntaje_documentacion=15,
            puntaje_precio=15
        )
        print(f"  ✓ Evaluación creada con puntaje: {evaluacion.puntaje}")
        
        # Crear un plan de mejoramiento en estado BORRADOR
        plan = PlanMejoramiento.objects.create(
            evaluacion=evaluacion,
            proveedor=proveedor_sin_usuario,
            estado='BORRADOR',
            analisis_causa='Análisis de prueba',
            acciones_propuestas='Acciones de prueba',
            responsable='Responsable de prueba',
            fecha_implementacion=date(2024, 12, 31),
            indicadores_seguimiento='Indicadores de prueba'
        )
        print(f"  ✓ Plan de mejoramiento creado en estado: {plan.estado}")
        
        # Cambiar el estado a FIRMADO_ENVIADO
        plan.estado = 'FIRMADO_ENVIADO'
        plan.save()
        print(f"  ✓ Estado cambiado a: {plan.estado}")
        
        # Recargar el proveedor para ver si se creó el usuario
        proveedor_sin_usuario.refresh_from_db()
        
        if proveedor_sin_usuario.user:
            print(f"  ✓ Usuario creado automáticamente: {proveedor_sin_usuario.user.username}")
            
            # Verificar el historial
            historial = HistorialEstado.objects.filter(
                plan=plan,
                estado_nuevo='USUARIO_CREADO'
            ).first()
            
            if historial:
                print("  ✓ Registro en historial creado")
                print(f"    Comentario: {historial.comentario[:100]}...")
            else:
                print("  ⚠ No se encontró registro en historial")
        else:
            print("  ✗ Usuario NO fue creado automáticamente")
            return False
        
        # Limpiar datos de prueba
        plan.delete()
        evaluacion.delete()
        if proveedor_sin_usuario.user:
            proveedor_sin_usuario.user.delete()
        proveedor_sin_usuario.delete()
        
        print("  ✓ Datos de prueba limpiados")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error durante la prueba: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("VERIFICACIÓN DE AJUSTES IMPLEMENTADOS")
    print("=" * 60)
    
    resultados = []
    
    # Ejecutar pruebas
    resultados.append(("Campo email_adicional", test_campo_email_adicional()))
    resultados.append(("Estado FIRMADO_ENVIADO", test_estado_firmado_enviado()))
    resultados.append(("Creación automática de usuario", test_creacion_automatica_usuario()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    todas_pasaron = True
    for nombre, resultado in resultados:
        estado = "✓ PASÓ" if resultado else "✗ FALLÓ"
        print(f"{nombre}: {estado}")
        if not resultado:
            todas_pasaron = False
    
    print("=" * 60)
    
    if todas_pasaron:
        print("\n✅ TODOS LOS AJUSTES FUNCIONAN CORRECTAMENTE")
        return 0
    else:
        print("\n❌ ALGUNOS AJUSTES REQUIEREN REVISIÓN")
        return 1


if __name__ == "__main__":
    sys.exit(main())