# middleware.py
import json
import threading
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user, logout
from django.shortcuts import redirect
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from .models import Auditoria
from django.urls import reverse

# Middleware para almacenar el request en thread local
request_local = threading.local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_local.request = request
        response = self.get_response(request)
        return response

class LoginRequiredMiddleware:
    """Middleware para redirigir usuarios no autenticados (Versión Corregida)"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas excluidas (calculadas dinámicamente para evitar problemas de URLs)
        excluded_paths = [
            settings.LOGIN_URL,
            reverse('GVS:password_reset'),  # Ruta de restablecimiento
            reverse('GVS:password_reset_done'),  # Ruta de confirmación
            '/static/',
            '/admin/'
        ]

        if not request.user.is_authenticated:
            # Verificar si la ruta actual está excluida
            path_is_excluded = any(
                request.path == path or 
                request.path.startswith(path)
                for path in excluded_paths
            )
            
            if not path_is_excluded:
                return redirect(settings.LOGIN_URL)
        
        return self.get_response(request)

class SessionTimeoutMiddleware:
    """Middleware para expiración de sesión (Versión Mejorada)"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo aplicar a usuarios autenticados
        if request.user.is_authenticated:
            current_time = timezone.now().timestamp()
            last_activity = request.session.get('last_activity')
            
            if last_activity and (current_time - last_activity > 300):
                logout(request)
                AuditoriaMiddleware.registrar_accion(
                    request, 
                    'S', 
                    'Sesión', 
                    detalles={'motivo': 'Timeout por inactividad'}
                )
                return redirect(settings.LOGIN_URL)
            
            request.session['last_activity'] = current_time
        
        return self.get_response(request)

class AuditoriaMiddleware:
    """Middleware para registro de auditoría"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Registrar intentos de login
        if request.path == settings.LOGIN_URL and request.method == 'POST':
            username = request.POST.get('username', 'desconocido')
            
            if response.status_code == 302:  # Login exitoso
                self.registrar_accion(
                    request, 
                    'L', 
                    'Sesión', 
                    detalles={
                        'username': username,
                        'resultado': 'éxito'
                    }
                )
            elif response.status_code == 200:  # Login fallido
                self.registrar_accion(
                    request, 
                    'I',  # Acción para intentos fallidos
                    'Sesión', 
                    detalles={
                        'username': username,
                        'resultado': 'fallo',
                        'error': self.get_login_error(response)
                    }
                )
        
        # Registrar logout
        elif request.path == settings.LOGOUT_URL:
            self.registrar_accion(
                request, 
                'S', 
                'Sesión',
                detalles={
                    'username': request.user.username if request.user.is_authenticated else 'anonimo'
                }
            )
        
        return response

    @classmethod
    def registrar_accion(cls, request, accion, modelo_afectado, id_objeto=None, detalles=None):
        """Registra acciones en la auditoría"""
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        detalles = detalles or {}
        
        try:
            Auditoria.objects.create(
                usuario=user,
                accion=accion,
                modelo_afectado=modelo_afectado,
                id_objeto=str(id_objeto) if id_objeto else None,
                detalles=json.dumps(detalles, cls=DjangoJSONEncoder),
                ip=cls.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                fecha=timezone.now()
            )
        except Exception as e:
            print(f"Error en auditoría: {str(e)}")
            cls.registrar_fallo_auditoria(user, detalles)

    @staticmethod
    def get_client_ip(request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR', '')
        
        if ip and ':' in ip and not ip.startswith('['):
            ip = ip.split(':')[0]
        
        return ip or '0.0.0.0'

    @staticmethod
    def get_login_error(response):
        """Extrae mensajes de error del contexto de respuesta"""
        try:
            return response.context_data['form'].errors.as_json()
        except (AttributeError, KeyError):
            return 'Error desconocido'

    @staticmethod
    def registrar_fallo_auditoria(user, detalles_original):
        """Registra fallos en el sistema de auditoría"""
        try:
            Auditoria.objects.create(
                usuario=user,
                accion='E',
                modelo_afectado='Auditoria',
                detalles=json.dumps({
                    'error': 'Fallo al registrar auditoría',
                    'detalles_originales': detalles_original
                }, cls=DjangoJSONEncoder),
                ip='0.0.0.0',
                user_agent='Sistema'
            )
        except Exception as e:
            print(f"Error crítico al registrar fallo de auditoría: {str(e)}")