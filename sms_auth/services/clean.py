from django.utils import timezone
from ..models import EmailCode


class CleanService:
    @classmethod
    def clear(cls):
        EmailCode.objects\
            .filter(valid_to__lt=timezone.now())\
            .delete()
