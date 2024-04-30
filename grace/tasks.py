import importlib
import datetime
from celery import shared_task

from grace.serializes import NurseOrderSerializer
from .models import NurseOrder, Wallet, NurseVisit, ErrorLogs
from .choices import OrderStatuses, CareType
from django.conf import settings
from user.models import User
from cloudpayments import CloudPayments
from cloudpayments.errors import CloudPaymentsError
from cloudpayments.models import Transaction
from .utils import bitrix_change_active, bitrix_change_processed
import decimal
import requests
from requests.auth import HTTPBasicAuth
import json
import os


cp = CloudPayments(settings.CLOUDPAYMENTS_PUBLIC_ID, settings.CLOUDPAYMENTS_PASSWORD)

def _send_topup_request(cp, endpoint, params=None, request_id=None):
    auth = HTTPBasicAuth(settings.CLOUDPAYMENTS_SALARY_PUBLIC_ID, settings.CLOUDPAYMENTS_SALARY_PASSWORD)
    headers = None
    
    with open('text.txt', 'w') as file:
        json.dump(params, file)

    os.system('openssl cms -sign -signer certificate.crt -inkey private.key -out sign.txt -in text.txt -outform pem')    

    f = open('sign.txt')
    lines = f.readlines()
    
    headers = {
        'X-Signature': ''.join(map(lambda x: x[:-1], lines[1:-1]))
    }



    if request_id is not None:
        headers['X-Request-ID'] = request_id
    
    response = requests.post(cp.URL + endpoint, json=params, auth=auth, headers=headers)
    print('SEND REQUEST', response.request.body,response.request.headers, response.request.hooks,)
    return response.json(parse_float=decimal.Decimal)


def topup(cp, params):
        print('PARAPMS', params)

        response = _send_topup_request(cp, 'payments/token/topup', params)
        print('RESPONSE TOPUP', response)


        if response['Success']:
           return Transaction.from_dict(response['Model'])
        raise CloudPaymentsError(response)


@shared_task
def sheduledPayment(paymentParams, transaction, amount):
    cp._send_request('payments/tokens/auth', paymentParams)



@shared_task
def acceptVisit(visit_id):
    visit = NurseVisit.objects.get(id=visit_id)
    user_wallet = Wallet.objects.get(user=visit.order.client)
    user_wallet.sendTo(visit.order.nurse.username, visit.order.cost)

@shared_task
def secondClientPayment(order, cost, accumId, transactionID):
    order = NurseOrder.objects.get(id=order['id'])
    client = User.objects.get(username=order.client)
    percent = 71

    if order.care_type == CareType.with_accommodation and order.status != OrderStatuses.in_archive:
        if len(order.accumalations.all()) > 4:
            percent = 91
        else:
            percent = 48

    params = {
            'Token': order.nurse.token,
            'Amount': round(cost*(percent/100),2),
            'AccountId': order.nurse.username,
            "InvoiceId": str(order.id),
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

    try:
        resp = cp.confirm_payment(transaction_id=int(transactionID), amount=cost)
        print(resp)
    except:
        ErrorLogs.objects.create(
            log='Ошибка подтверждения транзакции, она скорее всего была подтверждена ранее',
            user=order.nurse
        )
    try:
        response = topup(cp, params)
        print(response)
    except: ErrorLogs.objects.create(
            log='Ошибка ВЫПЛАТЫ исполнителю',
            user=order.nurse
        )

    
   
    if client.linked_card:
        order_cost = -1

        if order.care_type == CareType.with_accommodation and order.status == OrderStatuses.active:
            order_cost = order.cost
            
        if order.care_type == CareType.several_hours:
            if order.status == OrderStatuses.active:
                generated_visits = order.getCountVisitsPerWeek()
                order_cost = order.cost*generated_visits

            elif order.status == OrderStatuses.testing_period:
                if order.visits_count >= 1:
                    order.status = OrderStatuses.active
                    order.save()
                    bitrix_change_active(order.id, order.client)
                    
                
                if order.canGenerateNearestVisit():
                    order_cost = order.cost

        if order_cost != -1:  
            payment_params = {
                "Amount": order_cost,
                "Currency":"RUB",
                "InvoiceId": str(order.id),
                "Description":"Оплата товаров заказа" + str(order.id),
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
                },
                "Data": '{"isNurse": "False"}'
            }


            sheduledPayment.apply_async(
                kwargs = {'paymentParams': payment_params, 'transaction': transactionID, 'amount': order.cost},
                eta=  datetime.datetime.utcnow() + datetime.timedelta(hours=settings.DELTATIME_PAYMENT_CALLS)
            )
        # secondClientPayment.apply_async(
        #         kwargs = {'order': NurseOrderSerializer(order).data, },
        #         eta=  datetime.datetime.utcnow() + datetime.timedelta(days=settings.DELTATIME_ACTIVEPERIOD if order.status == OrderStatuses.active else settings.DELTATIME_TESTPERIOD )
        # )

    else:
        if order.status != OrderStatuses.in_archive:
            order.status = OrderStatuses.waiting
            order.save()
            bitrix_change_processed(order.id, cost=order.cost, user=order.client)



        
