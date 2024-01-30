import importlib
import datetime
from celery import shared_task

from grace.serializes import NurseOrderSerializer
from .models import NurseOrder, Wallet, NurseVisit
from .choices import OrderStatuses, CareType
from django.conf import settings
from user.models import User
from cloudpayments import CloudPayments
from cloudpayments.errors import CloudPaymentsError
from cloudpayments.models import Transaction
from .utils import bitrix_change_active, bitrix_change_processed


cp = CloudPayments(settings.CLOUDPAYMENTS_PUBLIC_ID, settings.CLOUDPAYMENTS_PASSWORD)



def topup(cp, params):
        print('PARAPMS', params)

        response = cp._send_request('payments/token/topup', params)
        print('RESPONSE TOPUP', response)


        if response['Success']:
           return Transaction.from_dict(response['Model'])
        raise CloudPaymentsError(response)


@shared_task
def sheduledPayment(paymentParams, transaction, amount):
    cp._send_request('payments/cards/auth', paymentParams)



@shared_task
def acceptVisit(visit_id):
    visit = NurseVisit.objects.get(id=visit_id)
    user_wallet = Wallet.objects.get(user=visit.order.client)
    user_wallet.sendTo(visit.order.nurse.username, visit.order.cost)

@shared_task
def secondClientPayment(order, cost, accumId, transactionID):
    order = NurseOrder.objects.get(id=order['id'])
    client = User.objects.get(username=order.client)
    percent = 35

    if order.care_type == CareType.with_accommodation and order.status != OrderStatuses.in_archive:
        if len(order.accumalations.all()) > 4:
            percent = 12
        else:
            percent = 40

    params = {
            'Token': order.nurse.token,
            'Amount': cost*(1 - percent/100),
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
                "AccumulationId": accumId, 
                "TransactionIds": [int(transactionID)],
                "EscrowType": "OneToN",
                "FinalPayout": True
            }
    }


    resp = cp.confirm_payment(transaction_id=int(transactionID), amount=cost)
    print(resp)        
    response = topup(cp, params)
    print(response)

    
   
    if client.linked_card:
        if order.status == OrderStatuses.active:
            generated_visits = order.getCountVisitsPerWeek()
            payment_params = {
                "Amount":order.cost * generated_visits,
                "Currency":"RUB",
                "InvoiceId":order.id,
                "Description":"Оплата товаров заказа" + order.id,
                "AccountId": order.client,
                "TrInitiatorCode": 0,
                "PaymentScheduled": 1,
                "Token":client.token,
                "Payer":
                { 
                    "FirstName":client.first_name,
                    "LastName":client.last_name,
                    "Address":order.address,
                    'Tel': client.username
                }
            }
            sheduledPayment.apply_async(
                kwargs = {'paymentParams': payment_params, 'transaction': transactionID, 'amount': order.cost * generated_visits },
                eta=  datetime.datetime.utcnow() + datetime.timedelta(hours=settings.DELTATIME_PAYMENT_CALLS)
            )

        if order.status == OrderStatuses.testing_period:
            if order.visits_count >= 1:
                order.status = OrderStatuses.active
                order.save()
                bitrix_change_active(order.id, order.client)
                
            
            if order.canGenerateNearestVisit():
                payment_params = {
                "Amount":order.cost,
                "Currency":"RUB",
                "InvoiceId":order.id,
                "Description":"Оплата товаров заказа" + order.id,
                "AccountId": order.client,
                "TrInitiatorCode": 0,
                "PaymentScheduled": 1,
                "Token":client.token,
                "Escrow":{
                    "StartAccumulation":True,
                    "EscrowType": 1
                },
                "Payer":
                { 
                    "FirstName":client.first_name,
                    "LastName":client.last_name,
                    "Address":order.address,
                    'Tel': client.username
                }
                }


                sheduledPayment.apply_async(
                    kwargs = {'paymentParams': payment_params, 'transaction': transactionID, 'amount': order.cost},
                    eta=  datetime.datetime.utcnow() + datetime.timedelta(hours=settings.DELTATIME_PAYMENT_CALLS)
                )
                
        secondClientPayment.apply_async(
                kwargs = {'order': NurseOrderSerializer(order).data},
                eta=  datetime.datetime.utcnow() + datetime.timedelta(days=settings.DELTATIME_ACTIVEPERIOD if order.status == OrderStatuses.active else settings.DELTATIME_TESTPERIOD )
        )

    else:
        if order.status != OrderStatuses.in_archive:
            order.status = OrderStatuses.waiting
            order.save()
            bitrix_change_processed(order.id, cost=order.cost, user=order.client)



        
