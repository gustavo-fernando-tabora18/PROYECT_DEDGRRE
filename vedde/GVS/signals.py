from django.db.models.signals import post_save, post_delete, pre_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import Auditoria, SolicitudVacaciones, Beneficio, Empleado, Solicitante
from datetime import date
from dateutil.relativedelta import relativedelta
from .middleware import request_local
import json
import os

User = get_user_model()

def get_current_user():
    """Obtiene el usuario actual de manera segura"""
    request = getattr(request_local, 'request', None)
    return request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None

def should_audit_model(sender):
    """Determina si un modelo debe ser auditado"""
    excluded_models = {'Auditoria', 'Session', 'LogEntry'}
    return sender.__name__ not in excluded_models and hasattr(sender, '_meta')

@receiver(pre_save)
def set_usuarios_creacion_modificacion(sender, instance, **kwargs):
    """Establece usuario creador y modificador"""
    if not should_audit_model(sender) or not hasattr(instance, 'creado_por'):
        return
        
    user = get_current_user()
    if not instance.pk and user:
        instance.creado_por = user
    elif user:
        instance.actualizado_por = user

def create_audit_log(user, action, model_name, instance, extra_details=None):
    """Crea registro de auditoría estandarizado"""
    try:
        detalles = {
            'modelo': model_name,
            'campos': {
                field.name: str(getattr(instance, field.name))
                for field in instance._meta.fields
                if field.name not in ['password', 'token']
            }
        }
        if extra_details:
            detalles.update(extra_details)
            
        Auditoria.objects.create(
            usuario=user,
            accion=action,
            modelo_afectado=model_name,
            id_objeto=instance.pk,
            detalles=json.dumps(detalles, ensure_ascii=False),
            ip=get_client_ip(getattr(request_local, 'request', None)),
            user_agent=get_user_agent(getattr(request_local, 'request', None))
        )
    except Exception as e:
        print(f"Error creating audit log: {e}")

def get_client_ip(request):
    """Obtiene IP del cliente de manera segura"""
    if not request:
        return '0.0.0.0'
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip.split(':')[0] if ':' in ip and not ip.startswith('[') else ip

def get_user_agent(request):
    """Obtiene User-Agent de manera segura"""
    return request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''

@receiver(post_save)
def registrar_creacion_actualizacion(sender, instance, created, **kwargs):
    """Registra creación/actualización de modelos"""
    if not should_audit_model(sender):
        return
    user = getattr(instance, 'actualizado_por', None) if not created else getattr(instance, 'creado_por', None)
    create_audit_log(user, 'C' if created else 'A', sender.__name__, instance)

@receiver(post_delete)
def registrar_eliminacion(sender, instance, **kwargs):
    """Registra eliminación de modelos"""
    if not should_audit_model(sender):
        return
    create_audit_log(get_current_user(), 'E', sender.__name__, instance)

@receiver(m2m_changed)
def registrar_cambios_m2m(sender, instance, action, pk_set, **kwargs):
    """Registra cambios en relaciones M2M"""
    if action not in ['post_add', 'post_remove', 'post_clear'] or not should_audit_model(instance.__class__):
        return
    
    extra_details = {
        'relacion': sender.__name__,
        'accion_m2m': action,
        'objetos_afectados': list(pk_set) if pk_set else None
    }
    create_audit_log(get_current_user(), 'M', instance.__class__.__name__, instance, extra_details)

@receiver(post_save, sender=Empleado)
def crear_beneficio_empleado(sender, instance, created, **kwargs):
    """Crea los beneficios iniciales al crear un empleado"""
    if created:
        Beneficio.objects.create(
            empleado=instance,
            dias_base=15,
            dias_adicionales=0,
            dias_tomados=0
        )

@receiver(pre_save, sender=SolicitudVacaciones)
def actualizar_beneficios_al_guardar(sender, instance, **kwargs):
    if not instance.pk:
        if instance.estado == 'APROBADA':
            instance.empleado.beneficios.actualizar_saldos(instance.dias_solicitados)
        return
        
    try:
        old_instance = SolicitudVacaciones.objects.get(pk=instance.pk)
        beneficio = instance.empleado.beneficios
        old_days = old_instance.dias_solicitados
        new_days = instance.dias_solicitados
        
        if old_instance.estado != 'APROBADA' and instance.estado == 'APROBADA':
            beneficio.actualizar_saldos(new_days)
        elif old_instance.estado == 'APROBADA' and instance.estado != 'APROBADA':
            beneficio.actualizar_saldos(-old_days)
        elif old_instance.estado == 'APROBADA' and instance.estado == 'APROBADA' and old_days != new_days:
            beneficio.actualizar_saldos(new_days - old_days)
    except ObjectDoesNotExist:
        pass

@receiver(post_delete, sender=SolicitudVacaciones)
def reintegrar_dias_al_eliminar(sender, instance, **kwargs):
    if instance.estado == 'APROBADA':
        instance.empleado.beneficios.actualizar_saldos(-instance.dias_solicitados)

