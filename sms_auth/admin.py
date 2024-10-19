from django.contrib.admin import ModelAdmin, register

from .models import *


@register(SMSMessage)
class SMSMessageAdmin(ModelAdmin):
    readonly_fields = (
        "created",
        "email",
    )

    def has_add_permission(self, request):
        return False


@register(EmailCode)
class EmailCodeAdmin(ModelAdmin):
    readonly_fields = (
        "valid_to",
        "created_at",
    )