from django.db import models
from django.utils.translation import gettext_lazy as _
from user.models import User
import uuid
from django import utils
from .choices import CareType, WeekDays, ChoiceArrayField, OrderStatuses
from django.contrib.postgres.fields import ArrayField
import datetime
from random import randint
from django.conf import settings

class Wallet(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    uuid = models.UUIDField(unique=True,  default=uuid.uuid4, editable=False)
    balance = models.IntegerField(_("Баланс"), default=0)
    user = models.OneToOneField(User, to_field='username', related_name='wallets', verbose_name=_("Пользователь"), on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Кошелек'
        verbose_name_plural = 'Кошельки'
    
    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} {self.balance} {self.id}'
    
    def sendWithoutTax(self, telephone:str, amount:int):
        user = User.objects.get(username=telephone)
        wallet = self.__class__.objects.get(user=user)

        self.balance -= amount
        self.save()

        wallet.balance += amount
        wallet.save()

    def sendTo(self, telephone:str, amount:int):
        user = User.objects.get(username=telephone)
        wallet = self.__class__.objects.get(user=user)
        prefs = TransferPrefs.objects.all()[0]
        
        if prefs.fixed_commission:
            self.balance -= amount
            wallet.balance += (amount - prefs.fixed_rate)
            prefs.root_wallet.balance += prefs.fixed_rate

            self.save()
            wallet.save()
            prefs.root_wallet.save()

        else:
            self.balance -= amount
            wallet.balance += (amount - amount*prefs.percent_rate/100)
            prefs.root_wallet.balance +=  amount*prefs.percent_rate/100

            self.save()
            wallet.save()
            prefs.root_wallet.save()

        
        
class TransferPrefs(models.Model):
    fixed_commission = models.BooleanField(_('Фиксированная комиссия'), default=False)
    fixed_rate = models.IntegerField(_('Фиксированная ставка'), default=100)
    percent_rate = models.IntegerField(_("Процентная ставка"), default=10)
    root_wallet = models.OneToOneField(Wallet, verbose_name=_("Корневой кошелек"), on_delete=models.CASCADE)
    
    class Meta:
        verbose_name='Настройка прибыли'
        verbose_name_plural = 'Настройки прибыли'
    


class NurseApplication(models.Model):
    id = models.UUIDField(primary_key=True,  default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, to_field='username', related_name='applications', verbose_name=_("Клиент"), on_delete=models.CASCADE)
    care_type = models.CharField(_("На какое время нужна сиделка?"), max_length=300, choices=CareType.choices, default=CareType.several_hours)
    time_start = models.CharField(_("Когда сиделка должна приступить к работе?"), max_length=300, default='')
    contact_type = models.CharField(_("Как с вами связаться?"), max_length=300, default='')
    active = models.BooleanField(_("Активная"), default=True)
    bitrix_id = models.IntegerField(_("ID в bitrix"), default=-1)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
    
    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} {self.user.username} {self.contact_type}'




class NurseOrder(models.Model):
    id = models.UUIDField( default=uuid.uuid4, editable=False, primary_key=True, )
    application = models.OneToOneField(NurseApplication, to_field='id', related_name='application_orders', verbose_name=_("Заявка"), on_delete=models.CASCADE)
    
    nurse = models.ForeignKey(User, to_field='username', related_name='nurse_orders', verbose_name=_("Сиделка"), on_delete=models.CASCADE)
    address = models.CharField(_("Адрес клиента"), max_length=300)
    comment = models.TextField(_("комментарий"), default='', )
    
    status = models.CharField(_("Статус заказа"), max_length=50, choices=OrderStatuses.choices, default=OrderStatuses.waiting)
    cost = models.PositiveIntegerField(_("Стоимость за посещение"))
    care_type = models.CharField(_("На какое время нужна сиделка?"), max_length=300, choices=CareType.choices, default=CareType.several_hours)
    
    @property
    def cost_per_week(self):
        if self.cost != None:
            if self.care_type == CareType.with_accommodation: return self.cost
            elif self.care_type == CareType.several_hours: return self.cost * len(self.days_to_visit)
        else: return 'Расчитаем после сохранения'

    @property
    def client(self):
        return self.application.user.username
    
    @property
    def days_to_visit(self):
        days = VisitDay.objects.all().filter(order=self)
        ans = []
        for day in days:
            ans.append([WeekDays(day.day).label , str(day.time_start)[:-3], str(day.time_end)[:-3]], )
        return ans
    
    @property
    def visits_count(self):
        days = NurseVisit.objects.all().filter(order=self)
        
        return len(days)
    visits_count.fget.short_description = 'Количество произведенных посещений'
    class Meta:
        verbose_name='Заказ'
        verbose_name_plural = 'Заказы'
    
    def  __str__(self):
        client = User.objects.get(username=self.client)
        return f'Клиент:{client.first_name} {client.last_name} Сиделка: {self.nurse.first_name} {self.nurse.last_name}'
    
    def generateNearestVisit(self):
        if self.care_type == CareType.several_hours and self.status != OrderStatuses.in_archive:
            now = datetime.date.today() + datetime.timedelta(days=1)
            days = VisitDay.objects.all().filter(order=self)
            visits = NurseVisit.objects.all().filter(order=self)
            week_days = []
            for day in days:
                week_days.append(day.day)

            while str(now.weekday()) not in week_days:
                now += datetime.timedelta(days=1)
            

            day = days.filter(day=str(now.weekday()))[0]

            flag = True
            for visit in visits:
                if visit.date == now: 
                    flag = False
            if flag:
                NurseVisit.objects.create(
                                order=self,
                                date=now,
                                time_start=day.time_start,
                                time_end=day.time_end

                )
                return True
            return False
            



    def generateVisitsPerWeek(self):
        if self.care_type == CareType.several_hours and self.status != OrderStatuses.in_archive:
            now = datetime.date.today() + datetime.timedelta(days=1)
            days = VisitDay.objects.all().filter(order=self)
            visits = NurseVisit.objects.all().filter(order=self)

            week_days = []
            for day in days:
                week_days.append(day.day)

            generated_visits = 0

            for _ in range(7):
                now += datetime.timedelta(days=1)
                
                if str(now.weekday()) in week_days:
                    day = days.filter(day=str(now.weekday()))[0]
                    flag = True
                    for visit in visits:
                        if visit.date == now: 
                            flag = False
                    
                    if flag:
                        generated_visits += 1
                        NurseVisit.objects.create(
                            order=self,
                            date=now,
                            time_start=day.time_start,
                            time_end=day.time_end                        
                        )
            return generated_visits
    
    

class VisitDay(models.Model):
    order = models.ForeignKey(NurseOrder, verbose_name=_("Заказ"), on_delete=models.CASCADE)
    day = models.CharField(_("День недели"), max_length=50, choices=WeekDays.choices, default=WeekDays.none)
    time_start = models.TimeField(_("Время начала посещения"), auto_now=False, auto_now_add=False, default=datetime.time(12,0))
    time_end =  models.TimeField(_("Время конца посещения"), auto_now=False, auto_now_add=False, default=datetime.time(13,0))
    
    class Meta:
        verbose_name = 'День посещения'
        verbose_name_plural = 'Дни посещения'

    def __str__(self):
        return f'{str(self.order)} {self.day}'
    
class NurseVisit(models.Model):
    id = models.UUIDField( default=uuid.uuid4, editable=False, primary_key=True, )
    order = models.ForeignKey(NurseOrder, related_name='visits', verbose_name=_("Заказ"), on_delete=models.CASCADE)
    date = models.DateField(_("Дата визита"), auto_now=False, auto_now_add=False)
    time_start = models.TimeField(_('Время начала'), auto_now=False, auto_now_add=False, default=datetime.time(12,0))
    time_end = models.TimeField(_('Время конца'),  auto_now=False, auto_now_add=False, default=datetime.time(13,0))
    completed = models.BooleanField(_('Посещение выполнено'), default=False)
    nursecomment = models.TextField(_("Комментарий сиделки"), default='нет')
    create_date = models.DateTimeField(_('Время Создания'),  auto_now_add=True)
    completed_date =  models.DateTimeField(_('Время выполнения'), auto_now=False, auto_now_add=False, default=datetime.date(2000,1,1))
    
    @property
    def nurse(self):
        return self.order.nurse.username

    class Meta:
        verbose_name = 'Посещение'
        verbose_name_plural = 'Посещения'
    
    def __str__(self) -> str:
        return f'{self.order}, {self.completed}'


class NurseAppelation(models.Model):
    id = models.UUIDField( default=uuid.uuid4, editable=False, primary_key=True)
    visit = models.ForeignKey(NurseVisit,to_field='id', related_name='appelations', verbose_name=_("Посещение"), on_delete=models.CASCADE)
    comment = models.TextField(_("Причина жалобы"))

    class Status(models.TextChoices):
        new = 'new', _('Новая')
        accepted = 'accepted', _("Удовлетворена")
        pending = 'pending', _('На рассмотрении')
        cancled = 'canceled', _('Отменена')

    status = models.CharField(_("Статус"), max_length=50, choices=Status.choices, default=Status.new)
    ans = models.TextField(_("Ответ администратора"))

    class Meta:
        verbose_name='Аппеляция визита'
        verbose_name_plural = 'Аппеляции визитов'

    def __str__(self) -> str:
        return f'{self.visit.order.client.first_name} {self.visit.order.client.last_name}, tel:{self.visit.order.client.username}, {self.status}'
    
    

    
    def acceptAppelation(self, ans):
        self.ans = ans
        self.status = self.Status.accepted
        self.save()
        root_wallet = TransferPrefs.objects.all()[0].root_wallet

        root_wallet.sendWithoutTax(self.visit.order.client.username, self.visit.order.cost)
        nurse_wallet = Wallet.objects.get(user=self.visit.order.nurse)
        nurse_wallet.sendWithoutTax(root_wallet.user.username, self.visit.order.cost)


class ErrorLogs(models.Model):
    date = models.DateTimeField(_('Время Создания'),  auto_now_add=True)
    log = models.JSONField(_("Лог"), default='')
    user = models.ForeignKey(User, to_field='username', related_name='logs', verbose_name=_("Пользователь"), on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = _("Лог ошибки")
        verbose_name_plural = _("Логи ошибок")

    def __str__(self):
        return str(self.date)
