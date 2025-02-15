from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model


from ..utils import random_code, valid_to

class SMSMessage(models.Model):
    """
    Save sended sms after as history
    """

    created = models.DateTimeField(auto_now_add=True)
    email = models.EmailField("Email", max_length=300)

    def __str__(self):
        return f"{self.email} / {self.created}"

    def __repr__(self):
        return f"{self.email}"

    class Meta:
        verbose_name = "Email log"
        verbose_name_plural = "Email logs"


class EmailCode(models.Model):
    """
    After validation save phone code instance
    """

    email = models.EmailField("Email", max_length=300, unique=True)
    owner = models.ForeignKey(get_user_model(),
                              null=True,
                              on_delete=models.CASCADE)
    code = models.PositiveIntegerField(default=random_code)
    valid_to = models.DateTimeField(default=valid_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Email code"
        verbose_name_plural = "Email codes"

    def __str__(self):
        return f"{self.email} ({self.code})"

    def __repr__(self):
        return self.__str__()

    @property
    def is_allow(self):
        return timezone.now() >= self.valid_to

    @property
    def message(self) -> str:
        return f"{self.code}"

    def save(self, *args, **kwargs):
        from ..conf import conf

        pretendent = self.__class__.objects.filter(
            email=self.email
        ).first()
        if pretendent is not None:
            self.pk = pretendent.pk

        if conf.SMS_AUTH_DEBUG_PHONE_NUMBER is not None:
            if self.email == conf.SMS_AUTH_DEBUG_PHONE_NUMBER:
                self.code = conf.SMS_DEBUG_CODE

        super().save(*args, **kwargs)
