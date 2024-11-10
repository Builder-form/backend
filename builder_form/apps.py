from django.apps import AppConfig


class BuilderFormConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'builder_form'
    def ready(self):
        from builder_form.listeners import increment_project
