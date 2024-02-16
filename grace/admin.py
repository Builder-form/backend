from django.contrib import admin
from .models import  NurseAppelation, NurseOrder, NurseVisit, NurseApplication, VisitDay, Wallet,  TransferPrefs, ErrorLogs, Accumulation
    
# Register your models here.
from user.models import CustomerInfo, NurseInfo, User
from django.core.exceptions import ValidationError
from django import forms


class NurseOrderForm(forms.ModelForm):
     def clean(self):
        nurse = self.cleaned_data['nurse']
        orders = NurseOrder.objects.all().filter(application=self.cleaned_data['application'])

        # if len(orders) == 1 and orders[0].application.id == self.cleaned_data['application'].id:
        #     raise forms.ValidationError({'application': "К этой заявки уже прикреплен заказ, выберите другую"})
        
        
        if nurse.role != User.Roles.nurse:
            raise forms.ValidationError({'nurse': "Роль пользователя не соответсвует полю"})


class DaysOrderInline(admin.TabularInline):
    model = VisitDay
    extra=0


@admin.register(NurseOrder)
class NurseOrderAdmin(admin.ModelAdmin):
    form = NurseOrderForm
    list_display = ('order_number', 'status', 'care_type',"client_info", "nurse_info", "cost",'id')
    inlines = [DaysOrderInline, ]
    def client_info(self,object):
        client = User.objects.get(username=object.client)

        return f'{client.username} {client.first_name} {client.last_name}'
    def nurse_info(self, object):
        return f'{object.nurse.username} {object.nurse.first_name} {object.nurse.last_name}'
    raw_id_fields = ['nurse', 'application' ]

    list_filter = ['status','care_type', 'nurse']
    fields = ["id",'status',  'visits_count', "application", 'client_info', 'nurse', 'address', 'cost','cost_per_week', 'care_type', 'comment',]
    readonly_fields = ('id', 'visits_count', 'client_info', 'cost_per_week', 'order_number')

    search_fields = [
    'nurse__username', 'nurse__last_name', 'nurse__first_name','order_number', 'id'
    ]



    

@admin.register(NurseApplication)
class NurseApplicationAdmin(admin.ModelAdmin):
    
    list_display = ['user_info', 'active','id']
    ordering = ('-active',)
    list_filter= ('active',)
    readonly_fields = ['id', 'bitrix_id']
    search_fields = ['user__username', 'user__last_name', 'user__first_name']
    def user_info(self,object):
        return f'{object.user.username} {object.user.first_name} {object.user.last_name}'



admin.site.register(Wallet)
admin.site.register(TransferPrefs)
admin.site.register(ErrorLogs)
admin.site.register(Accumulation)

@admin.register(NurseAppelation)
class NurseVisitsAdmin(admin.ModelAdmin):
    
    list_filter=['status',]
    list_display=['info','status',]

    def info(self, object):
        client = User.objects.get(username=object.visit.order.client)
        return f'Клиент: {client.first_name} {client.last_name}, tel:{client.username}'

@admin.register(NurseVisit)
class NurseVisitsAdmin(admin.ModelAdmin):
    list_filter=['completed',]
    list_display=['date', 'order', 'completed']
