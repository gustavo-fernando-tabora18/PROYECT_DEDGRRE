import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-2i%1rv&$b@=e-d@^wlxj4nc9!w_)yspq94@e75pa69(fxqo*rn'
DEBUG = True
ALLOWED_HOSTS = ['*']  # En producción restringir a dominios específicos

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'GVS.apps.GvsConfig',  # Configuración mejorada de la app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Internacionalización
    'GVS.middleware.SessionTimeoutMiddleware',  # Middleware para timeout de sesión
    'GVS.middleware.AuditoriaMiddleware',  # Middleware para auditoría

    'GVS.middleware.LoginRequiredMiddleware', 
    'GVS.middleware.RequestMiddleware',
]

ROOT_URLCONF = 'vedde.urls'
LOGOUT_URL = '/logout/'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# O si prefieres JSON, agrega esto:
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # Para archivos media
            ],
        },
    },
]

WSGI_APPLICATION = 'vedde.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ProyectGVS01',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",  # Mayor seguridad SQL
            'charset': 'utf8mb4',
        }
    }
}



# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-es'  # Español
TIME_ZONE = 'America/Tegucigalpa'  # Ajustar según zona horaria
USE_I18N = True
USE_L10N = True
USE_TZ = True
SESSION_COOKIE_AGE = 300
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True 
LANGUAGES = [
    ('es', _('Español')),
    ('en', _('Inglés')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Para producción
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (Archivos subidos por usuarios)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuraciones de seguridad adicionales (solo en producción)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

LOGIN_URL = '/login/'  # URL de la página de inicio de sesión
LOGIN_REDIRECT_URL = '/'  # Redirigir después del login
LOGOUT_REDIRECT_URL = '/login/'  # Redirigir después del logout

# Tamaños máximos para archivos (en bytes)
MAX_UPLOAD_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Configuración para usar un servidor SMTP real (por ejemplo, Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'tu_correo@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'tu_contraseña')