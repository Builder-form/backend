import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import NurseApplication, NurseOrder, ErrorLogs, User, NurseVisit,CreateNursePayment
from .utils import bitrix_add_lead, bitrix_change_active, bitrix_delete_lead, bitrix_change_processed
from django.contrib import messages # Here
from .choices import OrderStatuses
from datetime import datetime
from .tasks import topup, cp

@receiver(post_save, sender=NurseApplication, dispatch_uid=uuid.uuid4())
def application_saved(sender, instance, created, **kwargs):
    
    if created:
        ans = bitrix_add_lead(instance)
        instance.bitrix_id = int(ans)
        instance.save()
        
@receiver(post_save, sender=NurseOrder, dispatch_uid=uuid.uuid4())
def order_saved(sender, instance, created, **kwargs):
    # date_str = '02-29-2024'
    # date_object = datetime.strptime(date_str, '%m-%d-%Y').date()
    # NurseVisit.objects.create(
    #     order=instance,
    #     date=date_object,
    #     # time_start=datetime.time(10,0),
    #     # time_end=datetime.time(16,0)

    # )
    # print('CRAEATE')
    if instance.status == OrderStatuses.active:
        try:
            bitrix_change_active(instance.application.bitrix_id)
        except: 
            user = User.objects.get(username='admin')
            ErrorLogs.objects.create(
                log={'message':'Lead not in bitrix, errr. Error was in bitrix_change_process after save Order model'},
                user=user
            )
    else:
        try:
            bitrix_change_processed(instance.application.bitrix_id, instance.cost_per_week)
        except:
            user = User.objects.get(username='admin')
            ErrorLogs.objects.create(
                log={'message':'Lead not in bitrix, errr'},
                user=user
            )

    if created:
        ans = False
        try:
            bitrix_change_processed(instance.application.bitrix_id, instance.cost_per_week)
        except: 
            user = User.objects.get(username='admin')
            ErrorLogs.objects.create(
                log={'message':'Lead not in bitrix, errr'},
                user=user
            )
        instance.application.active = False
        instance.application.save()


@receiver(post_save, sender=CreateNursePayment, dispatch_uid=uuid.uuid4())
def order_saved(sender, instance, created, **kwargs):
    if created:
        order = instance.order
        acum = instance.accumulation
        params = {
                'Token': order.nurse.token,
                'Amount': instance.cost,
                'AccountId': order.nurse.username,
                'Currency': 'RUB',
                    "Payer": { 
                    "FirstName": order.nurse.first_name,
                    "LastName":  order.nurse.last_name,
                    "MiddleName": '-',
                    "Address": order.address,
                    "City":"MO",
                    "Country":"RU",
                    "Phone": order.nurse.username,
                },
                "Escrow": {
                    "AccumulationId": acum.escrowAccumulationId, 
                    "TransactionIds": [int(acum.transaction_id)],
                    "EscrowType": "OneToN",
                }
        }

        try:
            resp = cp.confirm_payment(transaction_id=int(acum.transaction_id))
            print('CONFIRM')
        except:
            ErrorLogs.objects.create(
                log='Ошибка подтверждения транзакции, она скорее всего была подтверждена ранее',
                user=order.nurse
            )
        
        try:
            response = topup(cp, params)
            print('RESP')
            instance.log = str(response)
        except: 
            instance.log = 'Ошибка ВЫПЛАТЫ исполнителю'
            ErrorLogs.objects.create(
                log='Ошибка ВЫПЛАТЫ исполнителю',
                user=order.nurse
            )
        instance.save()
