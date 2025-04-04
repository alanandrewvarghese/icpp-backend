from django.apps import AppConfig


class BadgesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.badges'

    def ready(self):
        # Import signals but don't execute database operations
        import apps.badges.signals
        # Remove any calls to create_default_badges() here
