from django.apps import AppConfig


class GraceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grace'

    def ready(self):
        from grace.listeners import order_saved, application_saved
