import importlib

from .conf import conf
from .models import EmailCode
from celery.contrib import rdb
from celery import shared_task


celery_conf = importlib.import_module(conf.SMS_CELERY_FILE_NAME)
app = getattr(celery_conf, "app")


def get_provider_class():
    provider = conf.SMS_PROVIDER
    print(provider, 'PROVIDER')
    return provider


@shared_task
def send_sms_async(identifier: int):
    code_instance = EmailCode.objects.filter(pk=identifier).first()
    if code_instance:
        provider_class = get_provider_class()
        provider = provider_class(
            to=str(code_instance.email), message=code_instance.message, conf=conf
        )
        provider.send_sms()
