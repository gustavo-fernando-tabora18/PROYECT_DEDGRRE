from django.contrib import admin
from .models import (
    Empresa, Estacion, Abanderado, Empleado, AsignacionEstacion,
    Vacante, Solicitante, Entrevistador, Entrevista, Auditoria, Informe,
    Beneficio, SolicitudVacaciones
)

# Resto del admin.py
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        'solicitante', 
        'empresa', 
        'status', 
        'fecha_contratacion', 
        'fecha_inactivacion',  # Nuevo campo
        'tipo_contrato',
        'antiguedad_display'  # Propiedad calculada
    )
    list_filter = ('status', 'empresa', 'tipo_contrato', 'fecha_contratacion')
    search_fields = ('solicitante__nombre', 'empresa__nombre')
    filter_horizontal = ('estaciones',)
    readonly_fields = ('antiguedad',)  # Propiedad de solo lectura
    date_hierarchy = 'fecha_contratacion'
    
    fieldsets = (
        ('Datos Básicos', {
            'fields': (
                'solicitante', 
                'empresa', 
                'fecha_contratacion',
                'antiguedad'  # Propiedad calculada
            )
        }),
        ('Estado', {
            'fields': (
                'status',
                'fecha_inactivacion',  # Nuevo campo
                'comentario_status'
            ),
            'description': 'Estado actual del empleado en el sistema'
        }),

    )

    def antiguedad_display(self, obj):
        return obj.antiguedad if obj.antiguedad else "N/A"
    
    antiguedad_display.short_description = 'Antigüedad'
    antiguedad_display.admin_order_field = 'fecha_contratacion'

    def get_readonly_fields(self, request, obj=None):
        """Hacer fecha_inactivacion editable solo para inactivos"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and obj.status != 'Inactivo':
            readonly.append('fecha_inactivacion')
        return readonly

    def save_model(self, request, obj, form, change):
        """Validación adicional para inactivación"""
        if obj.status == 'Inactivo' and not obj.fecha_inactivacion:
            from django.core.exceptions import ValidationError
            raise ValidationError("Debe especificar la fecha de inactivación")
        
        super().save_model(request, obj, form, change)

@admin.register(Entrevista)
class EntrevistaAdmin(admin.ModelAdmin):
    list_display = ('solicitante', 'entrevistador', 'fecha', 'estado')
    list_filter = ('estado', 'fecha', 'modalidad')
    search_fields = ('solicitante__nombre', 'entrevistador__nombre')
    raw_id_fields = ('solicitante', 'entrevistador', 'vacante')

@admin.register(Beneficio)
class BeneficioAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'saldo_disponible', 'dias_tomados')
    search_fields = ('empleado__solicitante__nombre',)
    autocomplete_fields = ['empleado']



# Modelos básicos
admin.site.register(Empresa)
admin.site.register(Estacion)
admin.site.register(Abanderado)
admin.site.register(AsignacionEstacion)
admin.site.register(Solicitante)
admin.site.register(SolicitudVacaciones)
admin.site.register(Vacante)
admin.site.register(Entrevistador)
admin.site.register(Auditoria)
admin.site.register(Informe)