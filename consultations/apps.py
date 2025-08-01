from django.apps import AppConfig


class ConsultationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consultations'
    
    def ready(self):
        """Import signals when the app is ready"""
        import consultations.signals
