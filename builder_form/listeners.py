import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project, APPSettings
from rest_framework.authtoken.models import Token



@receiver(post_save, sender=Project)
def increment_project(sender, instance=None, created=False, **kwargs):
    if created:
        # instance.user.projects_created += 1
        instance.user.save()