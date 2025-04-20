from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import F
from dateutil.relativedelta import relativedelta
from datetime import date
import os
from django.core.validators import RegexValidator
from django.utils.text import slugify
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.core.validators import RegexValidator
import hashlib



User = get_user_model()

class ModeloBase(models.Model):
    """
    Modelo base con campos comunes
    """
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    creado_por = models.ForeignKey(
        User,
        related_name='%(class)s_creados',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )
    actualizado_por = models.ForeignKey(
        User,
        related_name='%(class)s_actualizados',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )

    class Meta:
        abstract = True  # Esto hace que sea un modelo abstracto
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.__class__.__name__} - {self.creado_en}"

# Función externa al modelo (no indentada dentro de ModeloBase)
def documento_upload_path(instance, filename, doc_type):
    nombre_normalizado = slugify(instance.nombre)
    dni = instance.dni
    ext = filename.split('.')[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_unico = hashlib.md5(f"{dni}{timestamp}".encode()).hexdigest()[:6]
    return f'docs/{doc_type}/{dni}_{nombre_normalizado}_{hash_unico}_{timestamp}.{ext}'

def cv_upload_path(instance, filename):
    return documento_upload_path(instance, filename, "cv")

def foto_upload_path(instance, filename):
    return documento_upload_path(instance, filename, "fotos")

def antecedentes_penales_upload_path(instance, filename):
    return documento_upload_path(instance, filename, "antecedentes_penales")

def certificado_medico_upload_path(instance, filename):
    return documento_upload_path(instance, filename, "certificados_medicos")

def titulos_academicos_upload_path(instance, filename):
    return documento_upload_path(instance, filename, "titulos_academicos")

def certificado_ihss_upload_path(instance, filename):
    return documento_upload_path(instance, filename, "afiliacion_ihss")

def solicitud_empleo_upload_path(instance, filename):
    return documento_upload_path(instance, filename, "solicitudes_empleo")

class Empresa(ModeloBase):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField()

    class Meta(ModeloBase.Meta):
        verbose_name = 'Empresa'
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nombre

class Abanderado(ModeloBase):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Estacion(ModeloBase):
    nombre = models.CharField(max_length=255)
    ubicacion = models.TextField()
    correo_electronico = models.EmailField()
    telefono = models.CharField(max_length=20)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    abanderado = models.ForeignKey(Abanderado, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.empresa})"

class Solicitante(ModeloBase):
    def cv_upload_path(instance, filename):
        # Guardar siempre en la carpeta 'cv' con el nombre basado en el DNI
        ext = filename.split('.')[-1]  # Obtener la extensión del archivo
        return f'cv/{instance.dni}.{ext}'

    def foto_upload_path(instance, filename):
        # Guardar siempre en la carpeta 'fotos' con el nombre basado en el DNI
        ext = filename.split('.')[-1]  # Obtener la extensión del archivo
        return f'fotos/{instance.dni}.{ext}'

    dni = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField()
    edad = models.PositiveIntegerField()
    genero = models.CharField(max_length=10, choices=[
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Otro', 'Otro')
    ])
    fecha_nacimiento = models.DateField()
    cv = models.FileField(upload_to=cv_upload_path, blank=True, null=True)
    foto = models.ImageField(upload_to=foto_upload_path, blank=True, null=True)
    direccion = models.TextField()
    vacante = models.ForeignKey('Vacante', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} - {self.vacante}"

    def save(self, *args, **kwargs):
        # Guardar el objeto para obtener el ID si no existe
        if not self.id:
            super().save(*args, **kwargs)

        # Renombrar los archivos utilizando únicamente el DNI
        if self.cv and not self.cv.name.startswith(f'cv/{self.dni}'):
            ext = self.cv.name.split('.')[-1]  # Obtener la extensión del archivo
            self.cv.name = f'cv/{self.dni}.{ext}'

        if self.foto and not self.foto.name.startswith(f'fotos/{self.dni}'):
            ext = self.foto.name.split('.')[-1]  # Obtener la extensión del archivo
            self.foto.name = f'fotos/{self.dni}.{ext}'

        # Guardar nuevamente para aplicar los cambios
        super().save(*args, **kwargs)


class Vacante(ModeloBase):
    MODALIDAD_CHOICES = [
        ('Presencial', 'Presencial'),
        ('Remoto', 'Remoto'),
        ('Híbrido', 'Híbrido')
    ]
    TIPO_CONTRATO_CHOICES = [
        ('Tiempo completo', 'Tiempo completo'),
        ('Medio tiempo', 'Medio tiempo'),
        ('Temporal', 'Temporal')
    ]

    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    numero_vacantes = models.PositiveIntegerField()
    nivel_experiencia = models.CharField(max_length=100)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    departamento = models.CharField(max_length=100)
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES)
    fecha_maxima_postulacion = models.DateField()
    correo_contacto = models.EmailField()
    categoria = models.CharField(max_length=100)
    salario_ofrecido = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    estacion = models.ForeignKey(Estacion, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} - {self.empresa}"

class Empleado(ModeloBase):  # Asumo que ModeloBase es una clase abstracta personalizada (ej: campos comunes como id, fecha_registro, etc)
    TIPO_CONTRATO_CHOICES = [
        ('TIEMPO_COMPLETO', 'Tiempo completo'),
        ('MEDIO_TIEMPO', 'Medio tiempo'),
        ('TEMPORAL', 'Temporal')
    ]
    
    STATUS_EMPLEADO = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Pendiente', 'Pendiente')
    ]
    
    # Campos principales
    solicitante = models.OneToOneField(
        'Solicitante', 
        on_delete=models.CASCADE, 
        related_name='empleado'
    )
    fecha_contratacion = models.DateField(verbose_name='Fecha de contratación')
    tipo_contrato = models.CharField(
        max_length=20, 
        choices=TIPO_CONTRATO_CHOICES,
        verbose_name='Tipo de contrato'
    )
    empresa = models.ForeignKey(
        'Empresa', 
        on_delete=models.CASCADE,
        verbose_name='Empresa asociada'
    )
    estaciones = models.ManyToManyField(
        'Estacion', 
        through='AsignacionEstacion',
        verbose_name='Estaciones asignadas',
        blank=True 
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_EMPLEADO, 
        default='Pendiente',
        verbose_name='Estado del empleado'
    )
    comentario_status = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Comentario sobre el estado'
    )
    fecha_inactivacion = models.DateField(
        blank=True, 
        null=True,
        verbose_name='Fecha de inactivación (si aplica)'
    )

    # Métodos y propiedades
    def __str__(self):
        return f"{self.solicitante.nombre} - {self.empresa}"

    @property
    def esta_activo(self):
        return self.status == 'Activo'

    @property
    def antiguedad(self):
        # Validación básica para empleados inactivos
        if self.status == 'Inactivo' and not self.fecha_inactivacion:
            return "Error: Fecha de inactivación requerida"
        
        # Determina la fecha final de cálculo
        fecha_final = (
            date.today() 
            if self.status == 'Activo' 
            else self.fecha_inactivacion
        )

        # Validación de fechas inconsistentes
        if fecha_final < self.fecha_contratacion:
            return "Error: Fechas inválidas"
        
        # Cálculo de la diferencia
        delta = relativedelta(fecha_final, self.fecha_contratacion)
        años = delta.years
        meses = delta.months

        # Formato del resultado
        if años > 0:
            return f"{años} {'año' if años == 1 else 'años'}"
        return f"{meses} {'mes' if meses == 1 else 'meses'}"

    def estacion_actual(self):
        asignacion = self.asignacionestacion_set.filter(fecha_finalizacion__isnull=True).first()
        return asignacion.estacion if asignacion else None

    # Validaciones del modelo
    def clean(self):
        super().clean()
        
        # Valida fecha_inactivacion para empleados inactivos
        if self.status == 'Inactivo' and not self.fecha_inactivacion:
            raise ValidationError("Los empleados inactivos deben tener una fecha de inactivación.")
        
        # Valida que fecha_inactivacion no sea futura
        if self.fecha_inactivacion and self.fecha_inactivacion > date.today():
            raise ValidationError("La fecha de inactivación no puede ser en el futuro.")
        
        # Valida coherencia entre fechas
        if self.fecha_inactivacion and self.fecha_inactivacion < self.fecha_contratacion:
            raise ValidationError("La fecha de inactivación debe ser posterior a la fecha de contratación.")


    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['-fecha_contratacion']

class AsignacionEstacion(ModeloBase):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    estacion = models.ForeignKey(Estacion, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField(default=timezone.now)
    fecha_finalizacion = models.DateField(null=True, blank=True)
    es_responsable = models.BooleanField(default=False)

    class Meta(ModeloBase.Meta):
        ordering = ['-fecha_asignacion']

    def clean(self):
        if self.fecha_finalizacion and self.fecha_asignacion > self.fecha_finalizacion:
            raise ValidationError("La fecha de finalización no puede ser anterior a la de asignación")

    def __str__(self):
        return f"{self.empleado} en {self.estacion}"

class Entrevistador(ModeloBase):
    nombre = models.CharField(max_length=255)
    cargo = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField()

    def __str__(self):
        return f"{self.nombre} - {self.cargo}"

class Entrevista(ModeloBase):
    MODALIDAD_CHOICES = [
        ('Presencial', 'Presencial'),
        ('Virtual', 'Virtual')
    ]
    ESTADO_CHOICES = [
        ('Programada', 'Programada'),
        ('Realizada', 'Realizada'),
        ('Cancelada', 'Cancelada')
    ]

    asunto = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha = models.DateTimeField()
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    lugar = models.CharField(max_length=255)
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE)
    entrevistador = models.ForeignKey(Entrevistador, on_delete=models.CASCADE)
    solicitante = models.ForeignKey(Solicitante, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.asunto} - {self.fecha}"

class Auditoria(models.Model):
    ACCIONES = [
        ('C', 'Creación'),
        ('A', 'Actualización'),
        ('E', 'Eliminación'),
        ('L', 'Inicio de Sesión'),
        ('S', 'Cierre de Sesión'),
        ('I', 'Intento Fallido'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=1, choices=ACCIONES)
    modelo_afectado = models.CharField(max_length=50)
    id_objeto = models.CharField(max_length=20, null=True, blank=True)
    detalles = models.JSONField(default=dict)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'

    def __str__(self):
        return f"{self.get_accion_display()} - {self.modelo_afectado} - {self.usuario}"
    def get_absolute_url(self):
        return reverse('auditoria-detail', kwargs={'pk': self.pk})

class Informe(ModeloBase):
    FORMATO_CHOICES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('JSON', 'JSON')
    ]
    
    nombre = models.CharField(max_length=255)
    numero_pedido = models.CharField(max_length=50, unique=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='PDF')
    parametros = models.JSONField(default=dict)  # Para guardar filtros y configuraciones
    archivo = models.FileField(upload_to='informes/', null=True, blank=True)
    contenido = models.JSONField(default=list)  # Datos crudos del informe

    class Meta:
        ordering = ['-creado_en']
        verbose_name_plural = "Informes"

    def __str__(self):
        return f"{self.nombre} ({self.numero_pedido})"

class Beneficio(ModeloBase):
    empleado = models.OneToOneField(
        'Empleado',
        on_delete=models.CASCADE,
        related_name='beneficios',
        verbose_name='Empleado'
    )
    dias_base = models.PositiveIntegerField(
        default=10,
        verbose_name='Días Base Anuales',
        help_text='Días base según primer año de servicio (Art. 346 Código Trabajo)'
    )
    dias_adicionales = models.PositiveIntegerField(
        default=0,
        verbose_name='Días Adicionales',
        help_text='Días extras por antigüedad (+1 día por año después del primero)'
    )
    dias_tomados = models.PositiveIntegerField(
        default=0,
        verbose_name='Días Utilizados',
        help_text='Días de vacaciones ya consumidos'
    )

    class Meta:
        verbose_name = 'Beneficio de Vacaciones'
        verbose_name_plural = 'Beneficios de Vacaciones'
        ordering = ['empleado__solicitante__nombre']
        constraints = [
            models.CheckConstraint(
                check=models.Q(dias_tomados__lte=(models.F('dias_base') + models.F('dias_adicionales'))),
                name='check_dias_tomados_no_superan_total'
            )
        ]

    @property
    def saldo_disponible(self):
        """Calcula los días disponibles considerando base y adicionales"""
        return (self.dias_base + self.dias_adicionales) - self.dias_tomados

    @property
    def antiguedad_empleado(self):
        """Calcula los años completos de servicio del empleado"""
        hoy = date.today()
        delta = relativedelta(hoy, self.empleado.fecha_contratacion)
        return delta.years

    def actualizar_saldos(self, dias_solicitados):
        """
        Actualiza los días tomados tras una solicitud aprobada
        Args:
            dias_solicitados (int): Días a descontar
        Returns:
            bool: True si éxito, False si falla
        """
        try:
            if dias_solicitados > self.saldo_disponible:
                raise ValidationError(
                    f'Días solicitados ({dias_solicitados}) exceden el saldo disponible ({self.saldo_disponible})'
                )
            
            self.dias_tomados += dias_solicitados
            self.save()
            return True
        except Exception as e:
            # Loggear error en producción
            print(f"Error actualizando saldos: {str(e)}")
            return False

    def clean(self):
        """Valida que los días tomados no superen el total disponible"""
        super().clean()
        max_permitido = self.dias_base + self.dias_adicionales
        if self.dias_tomados > max_permitido:
            raise ValidationError({
                'dias_tomados': f'No puede superar el total disponible de {max_permitido} días'
            })

    def __str__(self):
        return f"{self.empleado} - {self.saldo_disponible} días disponibles"

    

#Loggin y usuario:
class SolicitudVacaciones(ModeloBase):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('CANCELADA', 'Cancelada'),
    ]

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='solicitudes_vacaciones'
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias_solicitados = models.PositiveIntegerField(editable=False)  # No editable, se calcula automáticamente
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    motivo_rechazo = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Solicitudes de Vacaciones"
        ordering = ['-creado_en']

    def __str__(self):
        return f"Solicitud #{self.id} - {self.empleado}"

    def clean(self):
        super().clean()
        
        # Validación 1: Fechas coherentes
        if self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de fin no puede ser anterior a la de inicio.")
        
        # Validación 2: No solapamiento de vacaciones aprobadas
        if self.estado == 'APROBADA':
            solapadas = SolicitudVacaciones.objects.filter(
                empleado=self.empleado,
                estado='APROBADA',
                fecha_inicio__lte=self.fecha_fin,
                fecha_fin__gte=self.fecha_inicio
            ).exclude(id=self.id)
            
            if solapadas.exists():
                raise ValidationError("El empleado ya tiene vacaciones aprobadas en este período.")

    def save(self, *args, **kwargs):
        # Calcular días automáticamente si no se especifican
        if not self.dias_solicitados:
            delta = self.fecha_fin - self.fecha_inicio
            self.dias_solicitados = delta.days + 1  # Incluye ambos días
        
        super().save(*args, **kwargs)