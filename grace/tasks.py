import importlib
import datetime
from celery import shared_task

from grace.serializes import NurseOrderSerializer
from .models import NurseOrder, Wallet
from .choices import OrderStatuses
from django.conf import settings
from user.models import User


@shared_task
def secondClientPayment(order):
    order = NurseOrder.objects.get(id=order['id'])
    client = User.objects.get(username=order.client)
    if client.linked_card:
        if order.status == OrderStatuses.active:
            generated_visits = order.generateVisitsPerWeek()
            if generated_visits:
                wallet = Wallet.objects.get(user=order.client)
                wallet.sendTo(order.nurse.username, order.cost_per_week)
        if order.status == OrderStatuses.testing_period:
            if order.visits_count >= 1:
                order.status = OrderStatuses.active
                order.save()
            if order.generateNearestVisit():
                wallet = Wallet.objects.get(user=order.client)
                wallet.sendTo(order.nurse.username, order.cost)

        secondClientPayment.apply_async(
                kwargs = {'order': NurseOrderSerializer(order).data},
                eta=  datetime.datetime.utcnow() + datetime.timedelta(days=settings.DELTATIME_ACTIVEPERIOD if order.status == OrderStatuses.active else settings.DELTATIME_TESTPERIOD )
        )
    else:
        order.status = OrderStatuses.waiting
        order.save()

        

        
