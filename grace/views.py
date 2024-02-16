from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions, status, generics

from grace.mixins import ResponsesMixin
from grace.utils import bitrix_change_archive, bitrix_change_processed, bitrix_change_active

from .choices import OrderStatuses, CareType
from .models import Wallet, TransferPrefs, NurseApplication, NurseOrder, NurseVisit, NurseAppelation, Accumulation
from .serializes import NurseApplicationSerializer, NurseOrderSerializer, NurseVisitSerializer, NurseAppelationSerializer
from django.http import Http404
from django import utils
from .tasks import secondClientPayment, acceptVisit
import datetime
from django.conf import settings
from user.models import User
import json
from cloudpayments import CloudPayments


cp = CloudPayments(settings.CLOUDPAYMENTS_PUBLIC_ID, settings.CLOUDPAYMENTS_PASSWORD)


#{
# care_type:str, 
# time_start:str,
# contact_type:str
# }
class NurseApplicationView(ResponsesMixin, generics.GenericAPIView):

    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseApplicationSerializer

    def get(self, request, format=None):
        applications = NurseApplication.objects.all().filter(user=request.user)
        serializer = self.serializer_class(applications, many=True)
        return self.success_objects_response(serializer.data)

    def post(self, request):
        data = request.data

        data['user'] = request.user.username

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.create_object_response(serializer.data)


class NurseApplicationDetail(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseApplicationSerializer

    def getApplication(self, id):
        try:
            return NurseApplication.objects.get(id=id)
        except: 
            return Http404

    def get(self,request, id, format=None):
        application = self.getApplication(id)
        serializer = self.serializer_class(application)
        return self.success_objects_response(serializer.data)
        
    def put(self,request, id, format=None):
        application = self.getApplication(id)
        serializer = self.serializer_class(application, data=request.data)

        if serializer.is_valid:
            serializer.save()
            return self.success_objects_response(serializer.data)
        else:
            return self.error_response(serializer.errors, request.user)

    def delete(self,request, id, format=None):
        application = self.getApplication(id)
        application.delete()
        return self.delete_response()
    
#{
# application:str, 
# client:str,
# nurse:str,
# address:str,
# cost:str,
# comment:str,
# }
class NurseOrderView(ResponsesMixin,generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseOrderSerializer
        
    def get(self,request, format=None):
        if request.user.role == 'customer':
            orders = NurseOrder.objects.all().filter(application__user=request.user.username)
        elif request.user.role == 'nurse':
            orders = NurseOrder.objects.all().filter(nurse=request.user)
        serializer = self.serializer_class(orders, many=True)
        return self.success_objects_response(serializer.data)
    def post(self, request):
        data = request.data

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.create_object_response(serializer.data)


class NurseOrderDetail(ResponsesMixin,generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseOrderSerializer

    def getOrder(self, id):
        try:
            return NurseOrder.objects.get(id=id)
        except: 
            return Http404

    def get(self,request, id, format=None):
        order = self.getOrder(id)
        serializer = self.serializer_class(order)
        data = serializer.data
        data['days'] = order.days_to_visit


        return self.success_objects_response(data)

    def put(self,request, id, format=None):
        order = self.getOrder(id)
        serializer = self.serializer_class(order, data=request.data)

        if serializer.is_valid:
            serializer.save()
            return self.success_objects_response(serializer.data)
        else:
            self.create_log(serializer.errors, request.user)
            return self.error_response(serializer.errors, request.user)

    def delete(self,request, id, format=None):
        order = self.getOrder(id)
        order.delete()
        return self.delete_response()
    

class NurseVisitView(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseVisitSerializer

    def post(self, request):
        data = request.data

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.success_objects_response(serializer.data)


#{
#  order: str, (order id)
#  date: DateField, 
#  time: TimeField,
#  nursecomment: str
# }


class NurseVisitsByOrder(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseVisitSerializer

    def get(self,request, order_id, format=None):
        visits = NurseVisit.objects.all().filter(order=order_id).order_by('completed', 'date').filter(order=order_id)
        serializer = self.serializer_class(visits, many=True)
        return self.success_objects_response(serializer.data)

#{
#  order: str, (order id)
#  date: DateField, 
#  time: TimeField,
#  completed: boolean
#  nursecomment: str
# }
class NurseVisitDetail(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseVisitSerializer
    def getVisit(self, id):
        try:
            return NurseVisit.objects.get(id=id)
        except: 
            return Http404

    def post(self, request, visit_id, format=None ):
        visit = self.getVisit(visit_id)

        visit.save()
        return self.simple_text_response('ok')



    def get(self,request, visit_id, format=None):
        visit = self.getVisit(visit_id)
        serializer = self.serializer_class(visit)
        return self.success_objects_response(serializer.data)
    
    def put(self,request, visit_id, format=None):
        visit = self.getVisit(visit_id)
        serializer = self.serializer_class(visit, data=request.data)
        print(request.data)
        

        if serializer.is_valid():
            if request.data['completed'] == True:
                visit.completed_date = utils.timezone.now()
                acceptVisit.apply_async(
                    kwargs = {'visit_id': visit_id},
                    eta =  datetime.datetime.utcnow() + datetime.timedelta(hours=settings.DELTATIME_PAYMENTNURSEPERIOD)
                )
            serializer.save()
            return self.success_objects_response(serializer.data)
        else:
            return self.error_response(serializer.errors, request.user)

    def delete(self,request, visit_id, format=None):
        visit = self.getVisit(visit_id)
        visit.delete()
        return self.delete_response()






class NurseAppelationView(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseAppelationSerializer


    def post(self, request):
        data = request.data

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return self.create_object_response(serializer.data)


#{
#  order: str, (order id)
#  date: DateField, 
#  time: TimeField,
#  nursecomment: str
# }
class NurseAppelationsByVisit(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseAppelationSerializer

    def get(self,request, visit_id, format=None):
        visits = NurseAppelation.objects.all().filter(visit=visit_id)
        serializer = self.serializer_class(visits, many=True)
        return self.success_objects_response(serializer.data)

#{
#  order: str, (order id)
#  date: DateField, 
#  time: TimeField,
#  completed: boolean
#  nursecomment: str
# }
class NurseAppelationDetail(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseAppelationSerializer
    def getAppelation(self, id):
        try:
            return NurseAppelation.objects.get(id=id)
        except: 
            return Http404

    def get(self,request, appelation_id, format=None):
        appelation = self.getAppelation(appelation_id)
        serializer = self.serializer_class(appelation)
        return self.success_objects_response(serializer.data)
    
    def put(self,request, appelation_id, format=None):
        appelation = self.getAppelation(appelation_id)
        serializer = self.serializer_class(appelation, data=request.data)

        if serializer.is_valid:
            serializer.save()
            return self.success_objects_response(serializer.data)
        else:
            return self.error_response(serializer.errors, request.user)

    def delete(self,request, appelation_id, format=None):
        appelation = self.getAppelation(id=appelation_id)
        appelation.delete()
        return self.delete_response()


class AcceptOrder(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseOrderSerializer

    def getOrder(self, id):
        try:
            return NurseOrder.objects.get(id=id)
        except: 
            return Http404

    def get(self,request, order_id, format=None):
        order = self.getOrder(order_id)


        if order.client != request.user.username:
            return self.error_methon_not_allowed_response('Вы пытаетесь оплатить чужой заказ, так быть не должно!', request.user)

        if order.status == OrderStatuses.waiting:
            if order.care_type == CareType.with_accommodation:
                return self.success_objects_response({"cost": order.cost})
            if order.visits_count < 1:
                if order.canGenerateNearestVisit():
                    return self.success_objects_response({"cost": order.cost})
                else: return self.error_methon_not_allowed_response('На эти даты уже есть посещения, нельзя оплатить повторно', request.user)

            else:
                generted_visits = order.getCountVisitsPerWeek()
                if generted_visits:
                    return self.success_objects_response({"cost": order.cost * generted_visits})
                else: return  self.error_methon_not_allowed_response('На эти даты уже есть посещения, нельзя оплатить повторно', request.user)
        
        else: 
            return self.error_methon_not_allowed_response('Заказ уже оплачен, сделать снова это нельзя!', request.user)

class MoveToArchiveOrder(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    def getOrder(self, id):
        try:
            return NurseOrder.objects.get(id=id)
        except: 
            return Http404

    def get(self,request, order_id, format=None):
        order = self.getOrder(order_id)
        
        if order.client != request.user.username:
            return self.error_methon_not_allowed_response('Чтобы отказаться от заказа обратитесь к менеджеру', request.user)

        visits = NurseVisit.objects.all().filter(order=order.id).filter(completed=False)

        now = datetime.datetime.today()
        flag = True
        
        for visit in visits:
            visit_time = datetime.datetime(visit.date.year, visit.date.month, visit.date.day, visit.time_start.hour, visit.time_start.minute, visit.time_start.second)
            delta = visit_time-now
            delta_hours = delta.seconds/3600 + delta.days*24
            
            if delta_hours < 8: 
                flag = False
        if flag:
            for visit in visits:
                if not visit.completed:
                    visit.delete()
                
            order.status = OrderStatuses.in_archive
            bitrix_change_archive(order.application.bitrix_id, order.client)
            order.save()
            return self.simple_text_response(f'Заказ id:{order.id} перемещен в архив!')
        else:
            return self.error_methon_not_allowed_response('До ближайшего визита менее, чем 8 часов! В целях избежания проблем, обратитесь к менеджеру для отмены заказа! Тел:+7 993 911 0350', request.user)
# {
#     sum:int
# }
class GetBalance(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    def post(self, request):
        if request.user.role == 'nurse':
            wallet = Wallet.objects.get_or_create(user=request.user)[0]
            summ = request.data['sum']
            if wallet.balance - summ < 0 or  summ < 0:
                return self.error_response({'message':'Недостаточно денег на счете!'}, request.user)

            else:
                wallet.balance -= summ
                wallet.save()
                return self.simple_text_response(f'Списано {summ} рублей')
        else:
            return self.error_response({'message':'У вас нет прав на это действие'} , request.user)




    def get(self, request):
        wallet = Wallet.objects.get_or_create(user=request.user)[0]
        return self.success_objects_response({'balance':str(wallet.balance)})


class GetVisitsByNurse(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseVisitSerializer



    def get(self, request):
        active_visits = NurseVisit.objects.all().filter(order__nurse=request.user).filter(completed=False).order_by('date').filter(completed=False)
        completed_visits = NurseVisit.objects.all().filter(order__nurse=request.user).filter(completed=True).order_by('-date').filter(completed=True)
        
        response = {
            "active_visits":[],
            "completed_visits":[] if completed_visits == None else self.serializer_class(completed_visits, many=True).data,
        }

        for visit in active_visits:
            flag = True
            for active_visit in response['active_visits']:
                if str(visit.date) == str(active_visit['date']):
                    active_visit['visits'].append(self.serializer_class(visit).data)
                    flag = False
            if flag:
                response['active_visits'].append({
                    'date': visit.date,
                    'visits': [self.serializer_class(visit).data]
                })

        
        return self.success_objects_response(response)



class CheckView(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = NurseOrderSerializer

    def getOrder(self, id):
        try:
            return NurseOrder.objects.get(id=id)
        except: 
            return False
    def post(self, request):
        if 'Data' in request.data.keys():
            data = json.loads(request.data['Data'])

            if data['isNurse'] == 'True':
                return self.success_objects_response({'code':0}) 

        order = self.getOrder(request.data['InvoiceId'])
        code = 0
        if order:
            print(request.data, order.client, order.client != request.data['AccountId'] )

            if order.client != request.data['AccountId']:
                code = 11
            if order.visits_count < 2:
                if order.cost != int(float(request.data['Amount'])):
                    code = 12
            else:
                if order.cost_per_week != int(float(request.data['Amount'])):
                    code = 12

        else:
            code = 10
        print(code, order.cost,order.cost, int(float(request.data['Amount'])), )
        if code != 0:
            self.create_log(log=f'Некорректные платежные запросы! code:{code}', user=User.objects.get(username=order.client))

        return self.success_objects_response({'code':code}) 
            
        


       

    # def get(self, request):
    #     return self.success_objects_response('ok')

class PayView(ResponsesMixin, generics.GenericAPIView):
    permission_classes = [
        permissions.AllowAny,
    ]
    authentication_classes = []
    serializer_class = NurseOrderSerializer

    def getOrder(self, id):
        try:
            return NurseOrder.objects.get(id=id)
        except:
            return False

    def post(self, request):
        print(request.data)
        order = self.getOrder(request.data['InvoiceId'])
        token = request.data['Token']
        accountId = request.data['AccountId']
        transaction = request.data['TransactionId']
        amount = float(request.data['PaymentAmount'])
        client = False

        try:
            client = User.objects.get(username=accountId)
        except:
            self.create_log('User not found во время выполнения транзакции оплаты',  User.objects.get(username='admin'))

        if client:
            if len(client.token) == 0:
                client.token = token
                client.save()

        print('DATA KEYS', request.data.keys())
        if 'Data' in request.data.keys():
            data = json.loads(request.data['Data'])
            if  data['isNurse'] == 'True' and client:
                client.linked_card = True
                client.save()
                r = cp.void_payment(transaction_id=transaction)
                print(r)
                return self.success_objects_response({"code":0})
        else:
            data = {}
            data['isNurse'] = 'False'



        accumId = request.data['EscrowAccumulationId']


        if order.status != OrderStatuses.in_archive and data['isNurse'] == 'False':
            if order.status == OrderStatuses.waiting:
                bitrix_change_active(order.id, order.client)

            if order.care_type == CareType.with_accommodation:
                wallet = Wallet.objects.get(user=order.client)
                wallet.sendTo(order.nurse.username, order.cost)
                order.status = OrderStatuses.active
                order.save()
                serializer = self.serializer_class(order)

                Accumulation.objects.create(
                    transaction_id = transaction,
                    amount = order.cost,
                    token = token,
                    order = order,
                    escrowAccumulationId = accumId,
                    сreatedDateIso = request.data['DateTime'],
                )
                secondClientPayment.apply_async(
                    kwargs = {'order': serializer.data, 'cost': order.cost, 'accumId':accumId, 'transactionID': transaction},
                    eta =  datetime.datetime.utcnow() + datetime.timedelta(days=settings.DELTATIME_ACTIVEPERIOD)- datetime.timedelta(hours=settings.DELTATIME_PAYMENT_CALLS)
                )
            
            elif order.care_type == CareType.several_hours:
                if order.visits_count < 1:
                    if order.generateNearestVisit():
                        wallet = Wallet.objects.get(user=order.client)
                        wallet.sendTo(order.nurse.username, order.cost)
                        order.status = OrderStatuses.testing_period
                        order.save()
                        serializer = self.serializer_class(order)
                        Accumulation.objects.create(
                            transaction_id = transaction,
                            amount = order.cost,
                            token = token,
                            order = order,
                            escrowAccumulationId = accumId,
                            сreatedDateIso = request.data['DateTime'],
                        )
                        secondClientPayment.apply_async(
                            kwargs = {'order': serializer.data, 'cost': order.cost, 'accumId':accumId, 'transactionID': transaction },
                            eta =  datetime.datetime.utcnow() + datetime.timedelta(days=settings.DELTATIME_TESTPERIOD) - datetime.timedelta(hours=settings.DELTATIME_PAYMENT_CALLS)
                        )
                
                else:
                    generted_visits = order.generateVisitsPerWeek()
                    if generted_visits:
                        wallet = Wallet.objects.get(user=order.client)

                        wallet.sendTo(order.nurse.username, order.cost*generted_visits)

                        order.status = OrderStatuses.active
                        order.save()

                        serializer = self.serializer_class(order)

                        Accumulation.objects.create(
                            transaction_id = transaction,
                            amount = order.cost * generted_visits,
                            token = token,
                            order = order,
                            escrowAccumulationId = accumId,
                            сreatedDateIso = request.data['DateTime'],
                        )

                        secondClientPayment.apply_async(
                            kwargs = {'order': serializer.data, 'cost': order.cost*generted_visits, 'accumId':accumId, 'transactionID': transaction},
                            eta =  datetime.datetime.utcnow() + datetime.timedelta(days=settings.DELTATIME_ACTIVEPERIOD)- datetime.timedelta(hours=settings.DELTATIME_PAYMENT_CALLS)
                        )
            
        return self.success_objects_response({"code":0})


class FailView(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = NurseOrderSerializer

    def getOrder(self, id):
        try:
            return NurseOrder.objects.get(id=id)
        except: 
            return False
    
    def post(self, request):
        order = self.getOrder(request.data['InvoiceId'])
        order.status = OrderStatuses.waiting
        order.save()
        bitrix_change_processed(order.id, order.cost, order.client)

        return self.success_objects_response({'code':0}) 