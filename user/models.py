from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _



class User(AbstractUser):

    class Roles(models.TextChoices):
        customer = 'customer',     _("Заказчик")
        nurse = 'nurse', _('Сиделка')
        admin = 'admin', _('Администратор')
        manager = 'manager', _('Менеджер')

    role = models.CharField(max_length=300, choices=Roles.choices, default=Roles.customer)
    token = models.CharField(_('Токен в cloudpayments для оплаты'),max_length=300, default='',)
    card_mask = models.CharField(_('Маска карты оплаты'),max_length=300, default='',)
    card_type = models.CharField(_('Тип карты'),max_length=300, default='',)
    telegram_username = models.CharField(_('Username в телеграм'), max_length=300, default='', blank=False)
    chat_telegram_id = models.CharField(_('ID чата с user в телеграм'), max_length=300, default='', blank=False)
    linked_card = models.BooleanField(_('Привязана ли карта'), default=False)
    

    
    @property
    def jwt_token(self):
        return str(Token.objects.get(user=self).key)
    



class CustomerInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    class Regions(models.TextChoices):
        msk = 'Москва',     _("Москва")
        mo = 'Московская область', _('Московская область')

    region = models.CharField(
        _("Регион"), 
        max_length=50, 
        choices=Regions.choices, 
        default=Regions.msk
    )

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} {self.user.username} {self.region}' 
    
    class Meta:
        verbose_name='Информация о клиенте'
        verbose_name_plural = 'Информация о клиентах'

class NurseInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    age = models.PositiveIntegerField(_("Возраст"))
    citizenship = models.CharField(_("Гражданство"), max_length=50)
    expirience = models.PositiveIntegerField(_("Опыт работы"))
    description = models.TextField(_("Описание"), max_length=1000)

    def __str__(self):
        return f' {self.user.first_name} {self.user.last_name} {self.age} лет {self.user.username} ' 

    class Meta:
        verbose_name='Информация о сиделке'
        verbose_name_plural = 'Информация о сиделках'