from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views  # Espacio después del punto
from django.contrib.auth import views as auth_views
from .views import password_reset_custom

app_name = 'GVS'

urlpatterns = [
    # Index
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Empresas
    path('empresa/', views.EmpresaListView.as_view(), name='empresa_list'),
    path('empresa/Crear/', views.EmpresaCreateView.as_view(), name='empresa_create'),
    path('empresa/Editar/<int:pk>/', views.EmpresaUpdateView.as_view(), name='empresa_update'),
    path('empresa/eliminar/<int:pk>/', views.EmpresaDeleteView.as_view(), name='empresa_delete'),
    
    # URLs para Abanderado
    path('abanderado/', views.AbanderadoListView.as_view(), name='abanderado_list'),
    path('abanderado/crear/', views.AbanderadoCreateView.as_view(), name='abanderado_create'),
    path('abanderado/editar/<int:pk>/', views.AbanderadoUpdateView.as_view(), name='abanderado_update'),
    path('abanderado/eliminar/<int:pk>/', views.AbanderadoDeleteView.as_view(), name='abanderado_delete'),


    path('estacion/', views.EstacionListView.as_view(), name='estacion_list'),
    path('estacion/Crear/', views.EstacionCreateView.as_view(), name='estacion_create'),
    path('estacion/Editar/<int:pk>/', views.EstacionUpdateView.as_view(), name='estacion_update'),
    path('estacion/Eliminar/<int:pk>/', views.EstacionDeleteView.as_view(), name='estacion_delete'),

    path('empleado/', views.EmpleadoListView.as_view(), name='empleado_list'),
    path('empleado/Crear/', views.EmpleadoCreateView.as_view(), name='empleado_create'),
    path('empleado/Editar/<int:pk>/', views.EmpleadoUpdateView.as_view(), name='empleado_update'),
    path('empleado/Eliminar/<int:pk>/', views.EmpleadoDeleteView.as_view(), name='empleado_delete'),

    path('solicitante/', views.SolicitanteListView.as_view(), name='solicitante_list'),
    path('solicitante/Crear/', views.SolicitanteCreateView.as_view(), name='solicitante_create'),
    path('solicitante/Editar/<int:pk>/', views.SolicitanteUpdateView.as_view(), name='solicitante_update'),
    path('solicitante/Eliminar/<int:pk>/', views.SolicitanteDeleteView.as_view(), name='solicitante_delete'),
    path('solicitante/Ver/<int:pk>/', views.SolicitanteDetailView.as_view(), name='solicitante_detail'),
    path('solicitante/descargar-cv/<int:solicitante_id>/', views.descargar_cv, name='descargar_cv'),

    path('vacante/', views.VacanteListView.as_view(), name='vacante_list'),
    path('vacante/Crear/', views.VacanteCreateView.as_view(), name='vacante_create'),
    path('vacante/Editar/<int:pk>/', views.VacanteUpdateView.as_view(), name='vacante_update'),
    path('vacante/Eliminar/<int:pk>/', views.VacanteDeleteView.as_view(), name='vacante_delete'),

    # URLs para Entrevistador
    path('entrevistador/', views.EntrevistadorListView.as_view(), name='entrevistador_list'),
    path('entrevistador/Crear/', views.EntrevistadorCreateView.as_view(), name='entrevistador_create'),
    path('entrevistador/Editar/<int:pk>/', views.EntrevistadorUpdateView.as_view(), name='entrevistador_update'),
    path('entrevistador/Eliminar/<int:pk>/', views.EntrevistadorDeleteView.as_view(), name='entrevistador_delete'),

    # URLs para Entrevista
    path('entrevista/', views.EntrevistaListView.as_view(), name='entrevista_list'),
    path('entrevista/Crear/', views.EntrevistaCreateView.as_view(), name='entrevista_create'),
    path('entrevista/Editar/<int:pk>/', views.EntrevistaUpdateView.as_view(), name='entrevista_update'),
    path('entrevista/Eliminar/<int:pk>/', views.EntrevistaDeleteView.as_view(), name='entrevista_delete'),

    path('auditoria/', views.AuditoriaListView.as_view(), name='auditoria_list'),
    path('auditoria/<int:pk>/', views.AuditoriaDetailView.as_view(), name='auditoria_detail'),

    # URLs para Beneficios
    path('beneficio/', views.BeneficioListView.as_view(), name='beneficio_list'),
    path('beneficio/crear/', views.BeneficioCreateView.as_view(), name='beneficio_create'),
    path('beneficio/editar/<int:pk>/', views.BeneficioUpdateView.as_view(), name='beneficio_edit'),
    path('beneficio/eliminar/<int:pk>/', views.BeneficioDeleteView.as_view(), name='beneficio_delete'),

    path('solicitud-vacaciones/', views.SolicitudVacacionesListView.as_view(), name='solicitud_vacaciones_list'),
    path('solicitud-vacaciones/crear/', views.SolicitudVacacionesCreateView.as_view(), name='solicitud_vacaciones_create'),
    path('solicitud-vacaciones/<int:pk>/editar/', views.SolicitudVacacionesUpdateView.as_view(), name='solicitud_vacaciones_update'),
    path('solicitud-vacaciones/<int:pk>/eliminar/', views.SolicitudVacacionesDeleteView.as_view(), name='solicitud_vacaciones_delete'),

    path('password_reset/', password_reset_custom, name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
]