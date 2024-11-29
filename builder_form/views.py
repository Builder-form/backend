from django.shortcuts import render
from builder_form.mixins import ResponsesMixin
from rest_framework import generics, permissions
from .models import Answer, AnswerTypes, AnswerQuestion, Project, Termin, APPSettings
from .serializers import QuestionInstanceSerializer,AnswerQuestionSerializer,AnswerSerializer, ProjectSerializer, TerminSerializer
from rest_framework import authentication, permissions, status, generics
import json
from django.conf import settings
from django.http import JsonResponse
import requests




class AnswerQuestionAPIView(ResponsesMixin, generics.GenericAPIView): #sample request {project_id:str, answers:{id: str, text:str}[]}
    authentication_classes = [authentication.TokenAuthentication]

    serializer_class = QuestionInstanceSerializer
    answer_serializer_class = AnswerQuestionSerializer
    a_serializer_class = AnswerSerializer
    termin_serializer_class = TerminSerializer

    def post(self, request, *args, **kwargs):
        answers = self.request.data['answers']
        project = Project.objects.get(pk=self.request.data['project_id'])

        for ans in answers:
            # ser = self.a_serializer_class(data=ans)
            # ser.is_valid(raise_exception=True)
            # ser.save()


            AnswerQuestion.objects.create(
                answer=Answer.objects.get(id=ans['id']),
                project=project,
                answer_text=ans['text'],
                question_instance = int(ans['question_instance'])
            )
            
        
        next_question = project.getNextQuestion()
        serializer = self.serializer_class(next_question)
        serializer_a = self.a_serializer_class(Answer.objects.all().filter(question__id=project.get_current_question().qid), many=True)
        serializer_termin = self.termin_serializer_class(Termin.objects.filter(qid=project.get_current_question().qid), many=True)
        data = serializer.data
        data['answers'] = serializer_a.data
        data['termins'] = serializer_termin.data
        data['progress'] = project.progress
        data['tree'] = json.dumps(project.tree)
        
        return self.success_objects_response(data)

class GetCurrentQuestionAPIView(ResponsesMixin, generics.GenericAPIView): #sample request {project_id:str}
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = QuestionInstanceSerializer
    answer_serializer_class = AnswerSerializer
    termin_serializer_class = TerminSerializer

    def post(self, request, *args, **kwargs):
        project = Project.objects.get(pk=self.request.data['project_id'])

        serializer_q = self.serializer_class(project.get_current_question())
        serializer_a = self.answer_serializer_class(Answer.objects.all().filter(question__id=project.get_current_question().qid), many=True)
        serializer_termin = self.termin_serializer_class(Termin.objects.all().filter(qid=project.get_current_question().qid), many=True)
        data = serializer_q.data
        data['answers'] = serializer_a.data
        data['termins'] = serializer_termin.data
        data['progress'] = project.progress
        data['tree'] = json.dumps(project.tree)

        return self.success_objects_response(data)

    
class GetProjectsAPIView(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]
 
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        projects = Project.objects.all().filter(user=request.user)
        serializer = self.serializer_class(projects, many=True)
        return self.success_objects_response(serializer.data)


class CreateProjectAPIView(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]

    serializer_class = ProjectSerializer

    def post(self, request):
        data = request.data
        data = request.data
        data['user'] = request.user.username
        # if request.user.projects_availables <= request.user.projects_created:
        #     return self.error_response('You created projects more than available to your acccount, please buy more projects')
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return self.create_object_response(serializer.data)


class GetAnswersAPIView(ResponsesMixin, generics.GenericAPIView):
    permission_classes = [
        permissions.AllowAny,
    ]
    
    def post(self, request, *args, **kwargs):
        project = Project.objects.get(pk=self.request.data['project_id'])

        data = project.tree
        data['name'] = project.name

        return self.success_objects_response(data)





class ProjectAPIView(ResponsesMixin, generics.GenericAPIView):
    authentication_classes = [authentication.TokenAuthentication]

    serializer_class = ProjectSerializer

    def get(self,request,id, format=None):
        try:
            project = Project.objects.get(id=id)
        except:
            return self.error_response('Invalid project ID')
        
        serializer = self.serializer_class(project)
        return self.success_objects_response(serializer.data)
    
    def put(self, request, id, format=None):
        try:
            project = Project.objects.get(id=id)
        except:
            return self.error_response('Invalid project ID')
        
        serializer = self.serializer_class(project, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success_objects_response(serializer.data)
        else:
            return self.error_response(serializer.errors)
     
    def delete(self,request,id, format=None):
        try:
            project = Project.objects.get(id=id)
        except:
            return self.error_response('Invalid project ID')
        
        project.delete()
        return self.delete_response()


class BackProjectAPIView(ResponsesMixin, generics.GenericAPIView):
    serializer_class = QuestionInstanceSerializer
    answer_serializer_class = AnswerSerializer
    termin_serializer_class = TerminSerializer

    def post(self, request, *args, **kwargs):
        project = Project.objects.get(pk=self.request.data['project_id'])

        previous_question  = project.back()

        serializer_q = self.serializer_class(previous_question)
        serializer_a = self.answer_serializer_class(Answer.objects.all().filter(question__id=previous_question.qid), many=True)
        serializer_termin = self.termin_serializer_class(Termin.objects.all().filter(qid=previous_question.qid), many=True)
        
        data = serializer_q.data
        data['answers'] = serializer_a.data
        data['termins'] = serializer_termin.data

        return self.success_objects_response(data)
    
class CreatePaymentView(ResponsesMixin, generics.GenericAPIView):
    def post(self, request):
        payment_settings = APPSettings.objects.all().filter(isActive=True)[0]
        client_id = settings.PAYPAL_CLIENT_ID
        secret = settings.PAYPAL_SECRET
        
        url = "https://api.sandbox.paypal.com/v2/checkout/orders"

        response = requests.post(
            "https://api.sandbox.paypal.com/v1/oauth2/token",
            auth=(client_id, secret),
            data={"grant_type": "client_credentials"},
        )
        access_token = response.json().get("access_token")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "GBP",
                        "value":  str(round(payment_settings.cost)),
                    }
                }
            ],
        }
        
        

        # response = requests.post(url, headers=headers, json=order_data)
        data = request.data
        data['user'] = request.user.username
        print(data)
        serializer = ProjectSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.create_object_response(serializer.data)
  

class ExecutePaymentView(ResponsesMixin, generics.GenericAPIView):
    permission_classes = [
        permissions.AllowAny,
    ]
    def post(self, request):
        payment_id = request.data.get("paymentID")
        payer_id = request.data.get("payerID")
        print(request.data, payment_id, payer_id)
        url = f"{settings.PAYPAL_API_URL}/v1/payments/payment/{payment_id}/execute"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " +settings.PAYPAL_ACCESS_TOKEN
        }
        execute_data = {
            "payer_id": payer_id
        }

        response = requests.post(url, headers=headers, data=json.dumps(execute_data))
        if response.status_code == 200: pass
            
        return JsonResponse(response.json(), status=response.status_code)