from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _



class User(AbstractUser):
    phone_number = models.CharField(_("phone_number"), max_length=50)
    # projects_availables = models.PositiveIntegerField(_('Availables projects'), default=0)
    # projects_created = models.PositiveIntegerField(_('Created projects'), default=0)
    
    @property
    def jwt_token(self):
        return str(Token.objects.get(user=self).key)
    
