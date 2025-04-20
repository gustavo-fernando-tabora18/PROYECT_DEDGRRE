from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Auditoria

User = get_user_model()

class SuccessMessageMixin:
    """
    Mixin optimizado para mensajes de éxito
    """
    success_message = ""
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            # Contexto base con el objeto y modelo
            context = {
                'object': self.object,
                'model': self.model._meta.verbose_name,
            }
            
            # Agregar campos dinámicos si existen
            if hasattr(self.object, 'empleado'):
                context['empleado'] = self.object.empleado  # Accede al empleado
            
            # Formatear el mensaje usando el contexto
            messages.success(
                self.request, 
                self.success_message % context
            )
        return response  


class DeleteMessageMixin:
    """
    Mixin optimizado para mensajes de eliminación
    """
    delete_success_message = ""
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        response = super().delete(request, *args, **kwargs)
        if self.delete_success_message:
            messages.success(
                request, 
                self.delete_success_message % {
                    'object': obj,
                    'model': self.model._meta.verbose_name
                }
            )
        return response

class AuditoriaMixin:
    """
    Mixin de auditoría optimizado
    """
    AUDIT_EXCLUDED_FIELDS = ['password', 'creado_en', 'actualizado_en']
    
    def registrar_auditoria(self, accion, instance, request=None):
        request = request or getattr(self, 'request', None)
        user = request.user if request and request.user.is_authenticated else None
        
        detalles = {
            'campos': self.obtener_detalles_campos(instance),
            'vista': self.__class__.__name__
        }
        
        Auditoria.objects.create(
            usuario=user,
            accion=accion,
            modelo_afectado=instance.__class__.__name__,
            id_objeto=str(instance.pk),
            detalles=detalles,
            ip=self.get_client_ip(request),
            user_agent=self.get_user_agent(request)
        )
    
    def obtener_detalles_campos(self, instance):
        return {
            field.name: str(getattr(instance, field.name))
            for field in instance._meta.fields
            if field.name not in self.AUDIT_EXCLUDED_FIELDS
        }
    
    @staticmethod
    def get_client_ip(request):
        if not request:
            return '0.0.0.0'
        xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip.split(':')[0] if ':' in ip and not ip.startswith('[') else ip
    
    @staticmethod
    def get_user_agent(request):
        return request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''

class AjaxResponseMixin:
    """
    Mixin para respuestas AJAX optimizado
    """
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data()
            }, status=400)
        return super().form_invalid(form)

    def form_valid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = {'success': True}
            if hasattr(self, 'get_ajax_data'):
                data.update(self.get_ajax_data())
            return JsonResponse(data)
        return super().form_valid(form)