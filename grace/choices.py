from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField
from django import forms

class CareType(models.TextChoices):
    several_hours = 'На несколько часов в день', _('На несколько часов в день')
    with_accommodation = 'C проживанием', _("C проживанием")

class WeekDays(models.TextChoices):
    none      = '-1',   _('Выберите день недели')
    monday    = '0',    _('Понедельник')
    tuesday   = '1',   _('Вторник')
    wednesday = '2', _('Среда')
    thursday  = '3',  _('Четверг')
    friday    = '4',    _('Пятница')
    saturday  = '5',  _('Суббота')
    sunday    = '6',    _('Воскресенье')

class OrderStatuses(models.TextChoices):
    waiting = 'Ожидание оплаты', _('Ожидание оплаты'),
    testing_period = 'Тестовый период', _('Тестовый период'),
    active = 'Активный', _('Активный'),
    in_archive = 'В архиве', _('В архиве')
    

class ChoiceArrayField(ArrayField):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.TypedMultipleChoiceField,
            'choices': self.base_field.choices,
            'coerce': self.base_field.to_python,
            'widget': forms.CheckboxSelectMultiple,
        }
        defaults.update(kwargs)

        return super(ArrayField, self).formfield(**defaults)