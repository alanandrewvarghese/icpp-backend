from django.apps import AppConfig

class StatusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.status'

    def ready(self):
        import apps.status.signals
