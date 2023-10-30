from django.apps import AppConfig

class UserConfig(AppConfig):
    name = 'user'
    verbose_name='user'
    
    def ready(self):
        from user.listeners import create_auth_token