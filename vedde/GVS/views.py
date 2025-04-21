from django.urls import reverse_lazy
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import render
from .models import *
from .forms import *
from .mixins import SuccessMessageMixin, DeleteMessageMixin
from django.utils.translation import gettext as _
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
import json

from django.utils.safestring import mark_safe
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_str

from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


#from xhtml2pdf import pisa
#import pandas as pd
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import date
from django.db import transaction

def home(request):
    if request.user.is_authenticated:
        return render(request, 'base.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('GVS:home')  # Redirige si ya está autenticado
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('GVS:home')  # Redirige al usuario autenticado
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def password_reset_custom(request):
    if request.method == 'POST':
        form = PasswordResetCustomForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Obtener usuario validado desde el formulario
                    user = User.objects.get(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email']
                    )
                    
                    # Generar contraseña segura
                    new_password = get_random_string(length=12) + "#Aa1"  # Ejemplo para complejidad
                    
                    try:
                        validate_password(new_password, user)
                    except ValidationError as e:
                        form.add_error(None, f"Error generando contraseña: {', '.join(e.messages)}")
                        return render(request, 'password_reset_form.html', {'form': form})

                    # Crear y enviar email con codificación UTF-8
                    email = EmailMessage(
                        subject='Restablecimiento de Contraseña - SOLEST',
                        body=f'''Hola {user.username},

Tu nueva contraseña temporal es: {new_password}

Por seguridad, te recomendamos cambiar esta contraseña después de iniciar sesión.

El equipo de SOLEST''',
                        from_email='noreply@solest.com',
                        to=[user.email],
                    )
                    email.encoding = 'utf-8'
                    email.send(fail_silently=False)

                    # Actualizar contraseña solo si todo salió bien
                    user.set_password(new_password)
                    user.save()

                    messages.success(request, '¡Contraseña actualizada! Revisa tu correo para obtener la nueva contraseña.')
                    return redirect('GVS:login')

            except Exception as e:
                form.add_error(None, f'Error al enviar el correo: {str(e)}')
    else:
        form = PasswordResetCustomForm()

    return render(request, 'password_reset_form.html', {'form': form})

# Nueva vista para descargar el CV de un solicitante
def descargar_cv(request, solicitante_id):
    try:
        solicitante = Solicitante.objects.get(id=solicitante_id)
        if solicitante.cv:
            return FileResponse(solicitante.cv.open('rb'), as_attachment=True, filename=solicitante.cv.name.split('/')[-1])
        else:
            return JsonResponse({'error': 'El solicitante no tiene un CV cargado.'}, status=404)
    except Solicitante.DoesNotExist:
        return JsonResponse({'error': 'Solicitante no encontrado.'}, status=404)

# EMPRESA
class EmpresaListView(ListView):
    model = Empresa
    template_name = 'GVS/empresa/index.html'
    context_object_name = 'empresas'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Listado de Empresas')
        return context

class EmpresaCreateView(CreateView):
    model = Empresa
    form_class = EmpresaForm
    success_url = reverse_lazy('GVS:empresa_list')
    template_name = 'GVS/empresa/crear.html'

    def form_valid(self, form):
        """Maneja respuestas AJAX y normales"""
        self.object = form.save()
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'empresa': {
                    'id': self.object.id,
                    'nombre': self.object.nombre,
                    'telefono': self.object.telefono,  # Campo directo
                    'correo': self.object.correo_electronico,
                    'direccion': self.object.direccion,
                    'texto_select': f"{self.object.nombre} ({self.object.telefono})"  # Texto formateado para el select
                }
            })
        
        return super().form_valid(form)

    def form_invalid(self, form):
        """Errores detallados para AJAX"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(),
                'error_summary': "Errores en: " + ", ".join(form.errors.keys())
            }, status=400)
            
        return super().form_invalid(form)


class EmpresaUpdateView(SuccessMessageMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'GVS/empresa/Editar.html'
    success_url = reverse_lazy('GVS:empresa_list')
    success_message = _('¡Cambios en "%(object)s" guardados correctamente!')

class EmpresaDeleteView(SuccessMessageMixin,DeleteView):
    model = Empresa
    template_name = 'GVS/empresa/Eliminar.html'
    success_url = reverse_lazy('GVS:empresa_list')
    success_message = _('¡Empresa "%(object)s" eliminado con éxito!')
    def get_success_message(self, cleaned_data):
        return _('¡Empresa "%(object)s" eliminada con éxito!')

# ABANDERADO
class AbanderadoListView(ListView):
    model = Abanderado
    template_name = 'GVS/abanderado/index.html'
    context_object_name = 'abanderados'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Listado de Abanderados')
        return context

class AbanderadoCreateView(SuccessMessageMixin, CreateView):
    model = Abanderado
    form_class = AbanderadoForm
    template_name = 'GVS/abanderado/crear.html'
    success_url = reverse_lazy('GVS:abanderado_list')
    success_message = "Abanderado creado exitosamente!"

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'abanderado': {
                    'id': self.object.id,
                    'nombre': self.object.nombre,
                    'texto': self.object.nombre
                }
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data()
            }, status=400)
        return super().form_invalid(form)

class AbanderadoUpdateView(SuccessMessageMixin, UpdateView):
    model = Abanderado
    form_class = AbanderadoForm
    template_name = 'GVS/abanderado/Editar.html'
    success_url = reverse_lazy('GVS:abanderado_list')
    success_message = _('¡Cambios en "%(object)s" guardados correctamente!')

class AbanderadoDeleteView(DeleteView):
    model = Abanderado
    template_name = 'GVS/abanderado/Eliminar.html'
    success_url = reverse_lazy('GVS:abanderado_list')
    
    def get_success_message(self, cleaned_data):
        return _('¡Abanderado "%(object)s" eliminado con éxito!')

# ESTACION
class EstacionListView(ListView):
    model = Estacion
    template_name = 'GVS/estacion/index.html'
    context_object_name = 'estaciones'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Listado de Estaciones')
        return context

class EstacionCreateView(SuccessMessageMixin, CreateView):
    model = Estacion
    form_class = EstacionForm
    template_name = 'GVS/estacion/crear.html'
    success_url = reverse_lazy('GVS:estacion_list')
    success_message = "Estación creada exitosamente!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_form'] = EmpresaForm()  # Formulario para modal
        context['abanderado_form'] = AbanderadoForm()  # Formulario para modal
        return context

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'estacion': {
                    'id': self.object.id,
                    'nombre': self.object.nombre,
                    # Puedes agregar otros campos necesarios
                }
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data(),
                'error_summary': "Errores en: " + ", ".join(form.errors.keys())
            }, status=400)
        return super().form_invalid(form)

class EstacionUpdateView(SuccessMessageMixin, UpdateView):
    model = Estacion
    form_class = EstacionForm
    template_name = 'GVS/estacion/Editar.html'
    success_url = reverse_lazy('GVS:estacion_list')
    success_message = _('¡Estación "%(object)s" actualizada correctamente!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_form'] = EmpresaForm()
        context['abanderado_form'] = AbanderadoForm()
        return context

class EstacionDeleteView(DeleteView):
    model = Estacion
    template_name = 'GVS/estacion/Eliminar.html'
    success_url = reverse_lazy('GVS:estacion_list')
    
    def get_success_message(self, cleaned_data):
        return _('¡Estación "%(object)s" eliminada con éxito!')

# EMPLEADO
class EmpleadoListView(LoginRequiredMixin, ListView):
    model = Empleado
    template_name = 'GVS/empleado/index.html'
    context_object_name = 'empleados'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'solicitante', 
            'empresa'
        )
        
        if not self.request.user.is_superuser:
            queryset = queryset.filter(status='Activo')
            
        return queryset.order_by('-fecha_contratacion')

class EmpleadoCreateView(CreateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'GVS/empleado/crear.html'
    success_url = reverse_lazy('GVS:empleado_list')

    @transaction.atomic
    def form_valid(self, form):
        try:
            
            self.object = form.save(commit=False)
            self.object.save()
            
            # Guardar relaciones M2M explícitamente
            form.save_m2m()

            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': str(self.success_url)
                })

            return super().form_valid(form)
                    
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': [str(e)]}
            }, status=500)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data()
            }, status=400)

        return super().form_invalid(form)
                
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solicitante_form'] = SolicitanteForm()  # Añadir formulario de empresa
    
        return context
    


class EmpleadoUpdateView(UpdateView):
    model = Empleado
    form_class = EmpleadoForm
    template_name = 'GVS/empleado/editar.html'
    success_url = reverse_lazy('GVS:empleado_list')
    
    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user
        response = super().form_valid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': str(self.get_success_url())
            })
        return response

    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'errors': form.errors.get_json_data()
        }, status=400)

class EmpleadoDeleteView(PermissionRequiredMixin, DeleteView):
    model = Empleado
    template_name = 'GVS/empleado/eliminar.html'
    success_url = reverse_lazy('GVS:empleado_list')
    permission_required = 'GVS.delete_empleado'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_eliminar'] = self.object.status in ['Inactivo', 'Pendiente']
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('¡Empleado eliminado con éxito!'))
        return super().delete(request, *args, **kwargs)

# SOLICITANTE
class SolicitanteListView(ListView):
    model = Solicitante
    template_name = 'GVS/solicitante/index.html'
    context_object_name = 'solicitantes'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Listado de Solicitantes')
        return context
    
class SolicitanteCreateView(SuccessMessageMixin, CreateView):
    model = Solicitante
    form_class = SolicitanteForm
    template_name = 'GVS/solicitante/Crear.html'
    success_url = reverse_lazy('GVS:solicitante_list')
    success_m= "¡Solicitante creado exitosamente!"
    
    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Renombrar y guardar los archivos únicamente con el DNI
        if self.object.cv:
            ext = self.object.cv.name.split('.')[-1]  # Obtener la extensión del archivo
            self.object.cv.name = f'cv/{self.object.dni}.{ext}'
        if self.object.foto:
            ext = self.object.foto.name.split('.')[-1]  # Obtener la extensión del archivo
            self.object.foto.name = f'fotos/{self.object.dni}.{ext}'

        self.object.save()
        return super().form_valid(form)

class SolicitanteUpdateView(SuccessMessageMixin, UpdateView):
    model = Solicitante
    form_class = SolicitanteForm
    template_name = 'GVS/solicitante/Editar.html'
    success_url = reverse_lazy('GVS:solicitante_list')
    success_message = _('¡Solicitante "%(object)s" actualizado correctamente!')
    
    def form_valid(self, form):
        self.object = form.save(commit=False)

        # Renombrar y guardar los archivos únicamente con el DNI
        if self.object.cv:
            ext = self.object.cv.name.split('.')[-1]  # Obtener la extensión del archivo
            self.object.cv.name = f'cv/{self.object.dni}.{ext}'
        if self.object.foto:
            ext = self.object.foto.name.split('.')[-1]  # Obtener la extensión del archivo
            self.object.foto.name = f'fotos/{self.object.dni}.{ext}'
        self.object.save()
        return super().form_valid(form)

class SolicitanteDeleteView(DeleteMessageMixin, DeleteView):
    model = Solicitante
    template_name = 'GVS/solicitante/Eliminar.html'
    success_url = reverse_lazy('GVS:solicitante_list')
    delete_success_message = _('¡Solicitante "%(object)s" eliminado con éxito!')

class SolicitanteDetailView(DetailView):
    model = Solicitante
    template_name = 'GVS/solicitante/Ver.html'  # Template para visualizar el solicitante
    context_object_name = 'solicitante'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Detalle del Solicitante')
        return context

# VACANTE
class VacanteListView(ListView):
    model = Vacante
    template_name = 'GVS/vacante/index.html'
    context_object_name = 'vacantes'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Listado de Vacantes')
        return context

class VacanteCreateView(SuccessMessageMixin, CreateView):
    model = Vacante
    form_class = VacanteForm
    template_name = 'GVS/vacante/Crear.html'
    success_url = reverse_lazy('GVS:vacante_list')
    success_message = _('¡Vacante "%(object)s" creada exitosamente!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_form'] = EmpresaForm()  # Añadir formulario de empresa
        context['estacion_form'] = EstacionForm()  # Añadir formulario de estación
        return context

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'vacante': {
                    'id': self.object.id,
                    'nombre': self.object.nombre,
                    'empresa': str(self.object.empresa) if self.object.empresa else '',
                    'estacion': str(self.object.estacion) if self.object.estacion else ''
                }
            })
        return super().form_valid(form)

class VacanteUpdateView(SuccessMessageMixin, UpdateView):
    model = Vacante
    form_class = VacanteForm
    template_name = 'GVS/vacante/Editar.html'
    success_url = reverse_lazy('GVS:vacante_list')
    success_message = _('¡Vacante "%(object)s" actualizada correctamente!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa_form'] = EmpresaForm()  # Añadir formulario de empresa
        context['estacion_form'] = EstacionForm()  # Añadir formulario de estación
        return context

class VacanteDeleteView(DeleteMessageMixin, DeleteView):
    model = Vacante
    template_name = 'GVS/vacante/Eliminar.html'
    success_url = reverse_lazy('GVS:vacante_list')
    delete_success_message = _('¡Vacante "%(object)s" eliminada con éxito!')

# ENTREVISTADOR
class EntrevistadorListView(ListView):
    model = Entrevistador
    template_name = 'GVS/entrevistador/index.html'
    context_object_name = 'entrevistadores'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Listado de Entrevistadores')
        return context

class EntrevistadorCreateView(SuccessMessageMixin, CreateView):
    model = Entrevistador
    form_class = EntrevistadorForm
    template_name = 'GVS/entrevistador/Crear.html'
    success_url = reverse_lazy('GVS:entrevistador_list')
    success_message = _('¡Entrevistador "%(object)s" creado exitosamente!')

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'entrevistador': {
                    'id': self.object.id,
                    'nombre': self.object.nombre
                }
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)
        return super().form_invalid(form)

class EntrevistadorUpdateView(SuccessMessageMixin, UpdateView):
    model = Entrevistador
    form_class = EntrevistadorForm
    template_name = 'GVS/entrevistador/Editar.html'
    success_url = reverse_lazy('GVS:entrevistador_list')
    success_message = _('¡Entrevistador "%(object)s" actualizado correctamente!')

class EntrevistadorDeleteView(DeleteMessageMixin, DeleteView):
    model = Entrevistador
    template_name = 'GVS/entrevistador/Eliminar.html'
    success_url = reverse_lazy('GVS:entrevistador_list')
    delete_success_message = _('¡Entrevistador "%(object)s" eliminado con éxito!')

# ENTREVISTA
class EntrevistaListView(ListView):
    model = Entrevista
    template_name = 'GVS/entrevista/index.html'
    context_object_name = 'entrevistas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Listado de Entrevistas')
        return context

class EntrevistaCreateView(SuccessMessageMixin, CreateView):
    model = Entrevista
    form_class = EntrevistaForm
    template_name = 'GVS/entrevista/Crear.html'
    success_url = reverse_lazy('GVS:entrevista_list')
    success_message = _('¡Entrevista creada exitosamente!')

    def form_valid(self, form):
        self.object = form.save()

        # Crear beneficio automáticamente si aplica
        if self.object.solicitante and not Beneficio.objects.filter(empleado__solicitante=self.object.solicitante).exists():
            empleado = Empleado.objects.filter(solicitante=self.object.solicitante).first()
            if empleado:
                Beneficio.objects.create(
                    empleado=empleado,
                    dias_base=15,
                    saldo_disponible=15
                )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entrevistador_form'] = EntrevistadorForm()
        context['vacante_form'] = VacanteForm()
        context['solicitante_form'] = SolicitanteForm()
        return context

class EntrevistaUpdateView(SuccessMessageMixin, UpdateView):
    model = Entrevista
    form_class = EntrevistaForm
    template_name = 'GVS/entrevista/Editar.html'
    success_url = reverse_lazy('GVS:entrevista_list')
    success_message = _('¡Entrevista actualizada correctamente!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entrevistador_form'] = EntrevistadorForm()
        return context

class EntrevistaDeleteView(DeleteMessageMixin, DeleteView):
    model = Entrevista
    template_name = 'GVS/entrevista/Eliminar.html'
    success_url = reverse_lazy('GVS:entrevista_list')
    delete_success_message = _('¡Entrevista eliminada con éxito!')

class AuditoriaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Auditoria
    template_name = 'GVS/auditoria/index.html'
    context_object_name = 'registros'
    paginate_by = 25
    permission_required = 'auditoria.view_auditoria'
    ordering = ['-fecha']

    ACCIONES_DISPONIBLES = {
        'C': 'Creación',
        'A': 'Actualización',
        'E': 'Eliminación',
        'L': 'Login Exitoso',  # Texto más descriptivo
        'S': 'Logout',
        'I': 'Intento Fallido'  # <- Clave corregida
    }

    def get_queryset(self):
        queryset = super().get_queryset().select_related('usuario')
        
        # Parámetros de búsqueda
        params = {
            'search': self.request.GET.get('q', ''),
            'modelo': self.request.GET.get('modelo', ''),
            'accion': self.request.GET.get('accion', ''),
            'fecha_inicio': self.request.GET.get('fecha_inicio', ''),
            'fecha_fin': self.request.GET.get('fecha_fin', ''),
            'usuario': self.request.GET.get('usuario', '')
        }

        # Filtro de búsqueda general
        if params['search']:
            queryset = queryset.filter(
                Q(modelo_afectado__icontains=params['search']) |
                Q(detalles__icontains=params['search']) |
                Q(ip__icontains=params['search']) |
                Q(usuario__username__icontains=params['search'])
            )

        # Filtros individuales
        if params['modelo']:
            queryset = queryset.filter(modelo_afectado=params['modelo'])
        if params['accion']:
            queryset = queryset.filter(accion=params['accion'])
        if params['usuario']:
            queryset = queryset.filter(usuario__username=params['usuario'])

        # Filtro por fechas
        if params['fecha_inicio'] and params['fecha_fin']:
            try:
                start_date = timezone.datetime.strptime(params['fecha_inicio'], '%Y-%m-%d')
                end_date = timezone.datetime.strptime(params['fecha_fin'], '%Y-%m-%d')
                queryset = queryset.filter(
                    fecha__date__range=(start_date, end_date))
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Opciones para los selectores
        context['modelos_disponibles'] = Auditoria.objects.order_by(
            'modelo_afectado'
        ).values_list('modelo_afectado', flat=True).distinct()
        context['acciones_disponibles'] = self.ACCIONES_DISPONIBLES
        
        # Para el selector de usuarios
        context['usuarios_disponibles'] = User.objects.filter(
            auditoria__isnull=False
        ).distinct().order_by('username')
        
        # Para mantener los filtros en los inputs
        context['current_search'] = {
            'q': self.request.GET.get('q', ''),
            'modelo': self.request.GET.get('modelo', ''),
            'accion': self.request.GET.get('accion', ''),
            'fecha_inicio': self.request.GET.get('fecha_inicio', ''),
            'fecha_fin': self.request.GET.get('fecha_fin', ''),
            'usuario': self.request.GET.get('usuario', '')
        }
        
        return context

class AuditoriaDetailView(LoginRequiredMixin, DetailView):
    model = Auditoria
    template_name = 'GVS/auditoria/detail.html'
    context_object_name = 'registro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formatear los detalles como JSON legible
        detalles = self.object.detalles
        if isinstance(detalles, str):
            try:
                detalles = json.loads(detalles)  # Intenta convertir si es cadena JSON
            except json.JSONDecodeError:
                pass
        
        context['detalles_formateados'] = mark_safe(
            json.dumps(detalles, indent=2, ensure_ascii=False) if detalles else None
        )
        
        return context

# BENEFICIO
class BeneficioListView(ListView):
    model = Beneficio
    template_name = 'GVS/beneficio/index.html'
    context_object_name = 'beneficios'
    paginate_by = 15
    ordering = ['empleado__solicitante__apellido']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Gestión de Beneficios de Vacaciones')
        return context

class BeneficioCreateView(SuccessMessageMixin, CreateView):
    model = Beneficio
    form_class = BeneficioForm
    template_name = 'GVS/beneficio/crear.html'
    success_url = reverse_lazy('GVS:beneficio_list')
    success_message = _('¡Beneficios creados para %(empleado)s!')

    def get_success_message(self, cleaned_data):
        empleado = self.object.empleado if hasattr(self.object, 'empleado') else None
        return self.success_message % {
            'empleado': str(empleado) if empleado else _('empleado desconocido')
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'dias_base': 15}
        return kwargs

class BeneficioUpdateView(SuccessMessageMixin, UpdateView):
    model = Beneficio
    form_class = BeneficioForm
    template_name = 'GVS/beneficio/editar.html'
    success_url = reverse_lazy('GVS:beneficio_list')
    success_message = _('¡Beneficios de %(empleado)s actualizados!')

    def get_success_message(self, cleaned_data):
        empleado = self.object.empleado if hasattr(self.object, 'empleado') else None
        return self.success_message % {
            'empleado': str(empleado) if empleado else _('empleado desconocido')
        }

class BeneficioDeleteView(SuccessMessageMixin, DeleteView):
    model = Beneficio
    template_name = 'GVS/beneficio/eliminar.html'
    success_url = reverse_lazy('GVS:beneficio_list')
    success_message = _('¡Beneficios de %(empleado)s eliminados!')

    def get_success_message(self, cleaned_data):
        empleado = self.object.empleado if hasattr(self.object, 'empleado') else None
        return self.success_message % {
            'empleado': str(empleado) if empleado else _('empleado desconocido')
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dias_restantes'] = self.object.saldo_disponible if self.object else 0
        return context

# SOLICITUD VACACIONES
class SolicitudVacacionesListView(LoginRequiredMixin, ListView):
    model = SolicitudVacaciones
    template_name = 'GVS/solicitud_vacaciones/index.html'
    context_object_name = 'solicitudes'
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset().select_related('empleado', 'empleado__solicitante')
        
        # Filtros para usuarios no administradores
        if not self.request.user.is_superuser:
            qs = qs.filter(empleado__usuario=self.request.user)
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
        
        return qs.order_by('-creado_en')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = SolicitudVacaciones.ESTADO_CHOICES
        context['current_estado'] = self.request.GET.get('estado', '')
        return context

class SolicitudVacacionesCreateView(SuccessMessageMixin, CreateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesForm
    template_name = 'GVS/solicitud_vacaciones/crear.html'
    success_url = reverse_lazy('GVS:solicitud_vacaciones_list')
    success_message = _('¡Solicitud creada exitosamente!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empleado_form'] = EmpleadoForm()
        return context

    def form_valid(self, form):
        fecha_inicio = form.cleaned_data['fecha_inicio']
        fecha_fin = form.cleaned_data['fecha_fin']
        form.instance.dias_solicitados = (fecha_fin - fecha_inicio).days + 1
        return super().form_valid(form)

class SolicitudVacacionesUpdateView(SuccessMessageMixin, UpdateView):
    model = SolicitudVacaciones
    form_class = SolicitudVacacionesAprobacionForm
    template_name = 'GVS/solicitud_vacaciones/editar.html'
    success_url = reverse_lazy('GVS:solicitud_vacaciones_list')
    success_message = _('¡Estado actualizado correctamente!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verificar si se pueden reintegrar días (si estaba aprobada)
        context['reintegrar_dias'] = self.object.estado == 'APROBADA'
        return context

class SolicitudVacacionesDeleteView(SuccessMessageMixin, DeleteView):
    model = SolicitudVacaciones
    template_name = 'GVS/solicitud_vacaciones/eliminar.html'
    success_url = reverse_lazy('GVS:solicitud_vacaciones_list')
    success_message = _('¡Solicitud eliminada!')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Verificar si se pueden reintegrar días (si estaba aprobada)
        context['reintegrar_dias'] = self.object.estado == 'APROBADA'
        return context