import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        group, group_created = Group.objects.get_or_create(name="Users")
        instance.groups.add(group)
        Token.objects.create(user=instance)
        instance.save()
        
        