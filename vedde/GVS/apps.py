from django.apps import AppConfig


class GvsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'GVS'
    def ready(self):
        import GVS.signals

