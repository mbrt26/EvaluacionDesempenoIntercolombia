"""
Señales para el sistema de planes de mejoramiento
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PlanMejoramiento, HistorialEstado, Proveedor
import string
import random
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=PlanMejoramiento)
def crear_usuario_proveedor_automatico(sender, instance, **kwargs):
    """
    Crear automáticamente el usuario del proveedor cuando el plan 
    cambia a estado FIRMADO_ENVIADO
    """
    # Solo procesar si es una actualización (no creación nueva)
    if instance.pk:
        try:
            # Obtener el estado anterior
            old_plan = PlanMejoramiento.objects.get(pk=instance.pk)
            
            # Verificar si el estado cambió a FIRMADO_ENVIADO
            if old_plan.estado != 'FIRMADO_ENVIADO' and instance.estado == 'FIRMADO_ENVIADO':
                
                # Verificar si el proveedor ya tiene usuario
                if not instance.proveedor.user:
                    # Generar contraseña temporal segura
                    caracteres = string.ascii_letters + string.digits + "!@#$%&*"
                    password_temporal = ''.join(random.choice(caracteres) for _ in range(12))
                    
                    # Usar el NIT como username
                    username = instance.proveedor.nit
                    
                    # Verificar que no exista el username
                    if not User.objects.filter(username=username).exists():
                        # Crear usuario Django
                        user = User.objects.create_user(
                            username=username,
                            email=instance.proveedor.email,
                            password=password_temporal,
                            first_name=instance.proveedor.razon_social[:30],
                        )
                        
                        # Actualizar el proveedor con el usuario creado
                        instance.proveedor.user = user
                        instance.proveedor.save()
                        
                        # Registrar en logs
                        logger.info(f"Usuario creado automáticamente para proveedor {instance.proveedor.razon_social} (NIT: {username})")
                        
                        # Guardar las credenciales en una tabla temporal o en el historial
                        # Por ahora solo registramos en el historial (sin contraseña por seguridad)
                        instance._credenciales_temporales = {
                            'username': username,
                            'password': password_temporal,
                            'email': instance.proveedor.email,
                            'email_adicional': instance.proveedor.email_adicional
                        }
                        
        except PlanMejoramiento.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f"Error al crear usuario automático: {str(e)}")


@receiver(post_save, sender=PlanMejoramiento)
def registrar_creacion_usuario(sender, instance, **kwargs):
    """
    Registrar en el historial cuando se crea un usuario automáticamente
    """
    # Verificar si se crearon credenciales temporales
    if hasattr(instance, '_credenciales_temporales'):
        creds = instance._credenciales_temporales
        
        # Crear registro en el historial
        HistorialEstado.objects.create(
            plan=instance,
            estado_anterior='SIN_USUARIO',
            estado_nuevo='USUARIO_CREADO',
            comentario=f'''Usuario creado automáticamente:
                Username: {creds['username']}
                Email principal: {creds['email']}
                Email adicional: {creds.get('email_adicional', 'N/A')}
                
                Nota: La contraseña temporal debe ser comunicada al proveedor de forma segura.'''
        )
        
        # Limpiar las credenciales temporales del objeto
        delattr(instance, '_credenciales_temporales')
        
        logger.info(f"Registro de creación de usuario completado para plan ID {instance.pk}")