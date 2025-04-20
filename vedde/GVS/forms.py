import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse_lazy
from django.forms.widgets import DateInput
from django.utils import timezone
from .models import Empresa, Abanderado, Estacion, Empleado, Solicitante, Vacante, Entrevistador, Entrevista, Beneficio, SolicitudVacaciones
from django.contrib.contenttypes.models import ContentType
from datetime import *
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
import os



from django.contrib.auth.models import User

# ==================== VALIDACIONES ====================
def validate_min_length(value, min_length, error_message=None):
    if value is None:
        return value
    stripped = value.strip()
    if len(stripped) < min_length:
        raise ValidationError(error_message or f"Mínimo {min_length} caracteres")
    return stripped

def validate_name(value, field_name="Nombre", min_length=3):
    cleaned = validate_min_length(value, min_length, f"{field_name} debe tener al menos {min_length} caracteres")
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúñÑ\s\-.&]+$', cleaned):
        raise ValidationError(f"{field_name} contiene caracteres inválidos")
    return cleaned

def validate_phone(value, country_code='+504', format_example='+504 XXXX-XXXX'):
    if not value:
        return value
    
    cleaned = value.strip()
    regex = rf'^{re.escape(country_code)}[\s-]?\d{{4}}[\s-]?\d{{4}}$'
    
    if not re.match(regex, cleaned):
        raise ValidationError(f"Formato inválido. Use: {format_example}")
    
    digits = re.sub(r'[\s-]', '', cleaned)[len(country_code):]
    return f"{country_code} {digits[:4]}-{digits[4:8]}"

def validate_email_custom(value):
    cleaned = value.strip()
    try:
        validate_email(cleaned)
        user, domain = cleaned.split('@')
        if not re.match(r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$', domain):
            raise ValidationError("Dominio inválido")
        return cleaned
    except (ValueError, ValidationError):
        raise ValidationError("Correo electrónico inválido")
    
# ==================== FORMULARIOS ====================
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'descripcion', 'direccion', 'telefono', 'correo_electronico']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Servicios Logísticos S.A.',
                'pattern': '.{3,100}',
                'title': '3-100 caracteres'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '',
                'pattern': '.{3,100}',
                'title': '3-100 caracteres'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'colonia, ciudad, etc.',
                'pattern': '.{3,100}',
                'title': '3-100 caracteres'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+504 XXXX-XXXX',
                'pattern': '^\+504[\s-]?\d{4}[\s-]?\d{4}$',
                'title': 'Ejemplo: +504 9999-9999'
            }),
            'correo_electronico': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'info@empresa.com',
                'pattern': '^[\w.-]+@[\w.-]+\.\w{2,}$'
            })
        }

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono']
        validate_phone(telefono)
        return telefono.replace(' ', '').replace('-', '')  # Normaliza a +504XXXXXXXX

    def clean_correo_electronico(self):
        correo = self.cleaned_data['correo_electronico']
        validate_email_custom(correo)
        return correo.strip().lower()  # Normaliza a minúsculas

class AbanderadoForm(forms.ModelForm):
    class Meta:
        model = Abanderado
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del abanderado'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Información relevante sobre el abanderado...'
            }),
        }
    
    def clean_nombre(self):
        return validate_name(self.cleaned_data['nombre'])

class EstacionForm(forms.ModelForm):
    class Meta:
        model = Estacion
        fields = ['nombre', 'ubicacion', 'telefono', 'correo_electronico', 'empresa', 'abanderado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Estación Shell Centro'
            }),
            'ubicacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ubicación geográfica exacta'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+504 XXXX-XXXX'
            }),
            'correo_electronico': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'estacion@empresa.com'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true',
                'title': 'Seleccione empresa...'
            }),
            'abanderado': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true',
                'title': 'Seleccione abanderado...'
            }),
        }
    
    def clean_nombre(self):
        return validate_name(self.cleaned_data['nombre'])
    
    def clean_telefono(self):
        return validate_phone(self.cleaned_data['telefono'])
    
    def clean_correo_electronico(self):
        return validate_email_custom(self.cleaned_data['correo_electronico'])

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'solicitante', 
            'fecha_contratacion', 
            'tipo_contrato',
            'empresa',
            'status',
            'fecha_inactivacion',  # Campo nuevo
            'comentario_status',
        ]
        widgets = {
            'solicitante': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true',
                'title': _('Seleccione un solicitante')
            }),
            'fecha_contratacion': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'placeholder': _('DD/MM/AAAA')
                }
            ),
            'tipo_contrato': forms.Select(attrs={
                'class': 'form-select',
                'data-style': 'btn-select'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-select',
                'data-ajax-url': '/api/empresas/'  # Si usas carga AJAX
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleInactivationDate(this)'  # JavaScript
            }),
            'fecha_inactivacion': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'disabled': 'disabled',
                    'placeholder': _('DD/MM/AAAA')
                }
            ),
            'comentario_status': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Ej: Motivo de inactivación...')
            }),
        }
        labels = {
            'fecha_inactivacion': _('Fecha de inactivación'),
        }
        help_texts = {
            'fecha_inactivacion': _('Requerido solo para estado Inactivo'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Lógica para el campo solicitante
        if not self.instance.pk:
            self.fields['solicitante'].queryset = Solicitante.objects.filter(
                empleado__isnull=True
            )
            self.fields['solicitante'].label = _('Solicitante (no empleados)')
        else:
            self.fields['solicitante'].queryset = Solicitante.objects.filter(
                pk=self.instance.solicitante.pk
            )
            self.fields['solicitante'].disabled = True
            self.fields['solicitante'].widget.attrs['class'] = 'form-control-plaintext'
        
        # Lógica para fecha_inactivacion
        if self.instance.status != 'Inactivo':
            self.fields['fecha_inactivacion'].disabled = True
            self.fields['fecha_inactivacion'].required = False
        else:
            self.fields['fecha_inactivacion'].disabled = False
            self.fields['fecha_inactivacion'].required = True

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        fecha_inactivacion = cleaned_data.get('fecha_inactivacion')
        fecha_contratacion = cleaned_data.get('fecha_contratacion')

        # Validación 1: Fecha inactivación requerida si está Inactivo
        if status == 'Inactivo' and not fecha_inactivacion:
            self.add_error(
                'fecha_inactivacion',
                _('Este campo es obligatorio para empleados inactivos.')
            )

        # Validación 2: Fechas coherentes
        if fecha_inactivacion and fecha_contratacion:
            if fecha_inactivacion < fecha_contratacion:
                self.add_error(
                    'fecha_inactivacion',
                    _('Debe ser posterior a la fecha de contratación')
                )
            
            if fecha_inactivacion > date.today():
                self.add_error(
                    'fecha_inactivacion',
                    _('No puede ser una fecha futura')
                )

        return cleaned_data

class SolicitanteForm(forms.ModelForm):
        class Meta:
            model = Solicitante
            fields = [
                'dni', 'nombre', 'telefono', 'correo_electronico',
                'edad', 'genero', 'fecha_nacimiento', 'cv', 'foto',
                'direccion', 'vacante'
            ]
            widgets = {
                'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el DNI'}),
                'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
                'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+504 XXXX-XXXX'}),
                'correo_electronico': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}),
                'edad': forms.NumberInput(attrs={'class': 'form-control', 'min': 18, 'max': 100, 'placeholder': 'Edad'}),
                'genero': forms.Select(attrs={'class': 'form-control'}),
                'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'DD/MM/AAAA'}),
                'cv': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
                'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
                'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa'}),
                'vacante': forms.Select(attrs={'class': 'form-control'}),
            }

        def clean_cv(self):
            cv = self.cleaned_data.get('cv')
            if cv:
                max_size = 5 * 1024 * 1024  # 5 MB
                if cv.size > max_size:
                    raise ValidationError("El archivo CV no puede exceder los 5 MB.")
                valid_extensions = ['.pdf', '.doc', '.docx']
                if not any(cv.name.endswith(ext) for ext in valid_extensions):
                    raise ValidationError("El archivo CV debe tener una de las siguientes extensiones: .pdf, .doc, .docx.")
            return cv

        def clean_foto(self):
            foto = self.cleaned_data.get('foto')
            if foto:
                max_size = 5 * 1024 * 1024  # 5 MB
                if foto.size > max_size:
                    raise ValidationError("La foto no puede exceder los 5 MB.")
                valid_extensions = ['.jpg', '.jpeg', '.png']
                if not any(foto.name.endswith(ext) for ext in valid_extensions):
                    raise ValidationError("La foto debe ser un archivo de imagen válido (.jpg, .jpeg, .png).")
            return foto

        def clean_telefono(self):
            telefono = self.cleaned_data.get('telefono')
            return validate_phone(telefono)

        def clean_correo_electronico(self):
            correo = self.cleaned_data.get('correo_electronico')
            return validate_email_custom(correo)

class VacanteForm(forms.ModelForm):
    class Meta:
        model = Vacante
        fields = ['nombre', 'descripcion', 'numero_vacantes', 'nivel_experiencia', 
                'modalidad', 'departamento', 'tipo_contrato', 'fecha_maxima_postulacion',
                'correo_contacto', 'categoria', 'salario_ofrecido', 'empresa', 'estacion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Gerente de Estación'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del puesto...'
            }),
            'numero_vacantes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2',
                'min': 1
            }),
            'nivel_experiencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Junior, Senior, etc.'
            }),
            'modalidad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'departamento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Recursos Humanos, Operaciones'
            }),
            'tipo_contrato': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_maxima_postulacion': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'correo_contacto': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'rh@empresa.com'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Técnico, Profesional'
            }),
            'salario_ofrecido': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'En Lempiras',
                'step': '0.01'
            }),
            'empresa': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true',
                'title': 'Buscar empresa...'
            }),
            'estacion': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true',
                'title': 'Buscar estación...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuración de choices para campos que los tienen
        self.fields['modalidad'].choices = [('', 'Seleccione modalidad...')] + Vacante.MODALIDAD_CHOICES
        self.fields['tipo_contrato'].choices = [('', 'Seleccione tipo de contrato...')] + Vacante.TIPO_CONTRATO_CHOICES
        
        # Configuración de querysets para relaciones
        self.fields['empresa'].queryset = Empresa.objects.all()
        self.fields['estacion'].queryset = Estacion.objects.all()
    
    def clean_nombre(self):
        return validate_name(self.cleaned_data['nombre'])
    
    def clean_correo_contacto(self):
        return validate_email_custom(self.cleaned_data['correo_contacto'])

class EntrevistadorForm(forms.ModelForm):
    class Meta:
        model = Entrevistador
        fields = ['nombre', 'cargo', 'telefono', 'correo_electronico']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Gerente de RH'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+504 XXXX-XXXX'
            }),
            'correo_electronico': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'entrevistador@empresa.com'
            }),
        }
    
    def clean_nombre(self):
        return validate_name(self.cleaned_data['nombre'])
    
    def clean_telefono(self):
        return validate_phone(self.cleaned_data['telefono'])
    
    def clean_correo_electronico(self):
        return validate_email_custom(self.cleaned_data['correo_electronico'])

class EntrevistaForm(forms.ModelForm):
    class Meta:
        model = Entrevista
        fields = ['asunto', 'descripcion', 'fecha', 'modalidad', 'estado', 
                'lugar', 'vacante', 'entrevistador', 'solicitante']
        widgets = {
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Entrevista técnica para puesto de cajero'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalles de la entrevista...'
            }),
            'fecha': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'modalidad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'lugar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección o enlace virtual'
            }),
            'vacante': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true'
            }),
            'entrevistador': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true'
            }),
            'solicitante': forms.Select(attrs={
                'class': 'form-select selectpicker',
                'data-live-search': 'true'
            }),
        }

class BeneficioForm(forms.ModelForm):
    class Meta:
        model = Beneficio
        fields = ['empleado', 'dias_base', 'dias_adicionales', 'dias_tomados']
        widgets = {
            'empleado': forms.HiddenInput(),  # Cambiado a campo oculto
            'dias_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'style': 'max-width: 150px;',
                'placeholder': 'Ej. 10'
            }),
            'dias_adicionales': forms.NumberInput(attrs={
                'class': 'form-control bg-light',
                'readonly': True,
                'style': 'max-width: 150px;'
            }),
            'dias_tomados': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'style': 'max-width: 150px;',
                'placeholder': 'Ej. 5'
            })
        }
        help_texts = {
            'dias_base': 'Mínimo 10 días según legislación hondureña',
            'dias_adicionales': 'Calculado automáticamente por antigüedad',
            'dias_tomados': f'Máximo permitido: base + adicionales'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance.pk:
            # Permitir el empleado actual en el queryset
            self.fields['empleado'].queryset = Empleado.objects.filter(
                Q(beneficios__isnull=True) | Q(pk=self.instance.empleado.pk)
            )
            
            # Configurar máximo dinámico para días tomados
            max_permitido = self.instance.dias_base + self.instance.dias_adicionales
            self.fields['dias_tomados'].widget.attrs['max'] = max_permitido
            
            # Bloquear campos calculados
            self.fields['dias_adicionales'].disabled = True
        else:
            # Configuración para nuevos registros
            self.fields['empleado'].widget = forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione un empleado'
            })
            self.fields['empleado'].queryset = Empleado.objects.filter(beneficios__isnull=True)
            self.fields['dias_tomados'].widget.attrs['max'] = 10  # Valor base inicial

    def clean(self):
        cleaned_data = super().clean()
        dias_base = cleaned_data.get('dias_base', 0)
        dias_adicionales = cleaned_data.get('dias_adicionales', 0)
        dias_tomados = cleaned_data.get('dias_tomados', 0)
        
        # Validación de días base mínimo
        if dias_base < 10:
            self.add_error('dias_base', 'El mínimo legal es 10 días (Art. 346 Código Trabajo)')
        
        # Validación de días tomados vs total disponible
        if dias_tomados > (dias_base + dias_adicionales):
            error_msg = f"Días usados ({dias_tomados}) superan el total disponible ({dias_base + dias_adicionales})"
            self.add_error('dias_tomados', error_msg)
        
        return cleaned_data

# ==================== VACACIONES ====================
# forms.py
class SolicitudVacacionesForm(forms.ModelForm):
    class Meta:
        model = SolicitudVacaciones
        fields = ['empleado', 'fecha_inicio', 'fecha_fin']  # Ahora incluye empleado
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

class SolicitudVacacionesAprobacionForm(forms.ModelForm):
    class Meta:
        model = SolicitudVacaciones
        fields = ['estado', 'motivo_rechazo']
        widgets = {
            'motivo_rechazo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ingrese el motivo...'}),
        }

class PasswordResetCustomForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if username and email:
            if not User.objects.filter(username=username, email=email).exists():
                self.add_error(None, 'Usuario o correo electrónico incorrecto')
        
        return cleaned_data