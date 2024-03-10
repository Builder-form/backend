from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions, status
from .models import CustomerInfo, NurseInfo, User
from .serializers import NurseInfoSerializer, CustomerInfoSerializer, UserSerializer
from django.http import Http404


# Пример body post запроса
# {
#     user:{
#         first_name:str,
#         last_name:str,
#         role:str,
#         email:str,
#     }
#     nurse_info:{
#         age:int, 
#         citizenship:str,
#         expirience:str,
#         description:str
#     }
# }


class UserMeView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = UserSerializer

    def get(self,request, format=None):
        serializer = self.serializer_class(request.user)
        
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
        )

class UserView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = UserSerializer

    def getInfo(self, user):
        try:
            return User.objects.get(username=user)
        except NurseInfo.DoesNotExist:
            raise Http404("Нет такого пользователя")

    def get(self,request, tel, format=None):
        info = self.getInfo(user=tel)
        serializer = self.serializer_class(info)

        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
        )

    
class NurseInfoView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseInfoSerializer


    def getInfo(self, user):
        try:
            return NurseInfo.objects.get(user=user)
        except NurseInfo.DoesNotExist:
            raise Http404("Нет такого пользователя")

    def post(self, request):
        data = request.data
        if data['user']['telegram_username'] == '':
             data['user']['telegram_username'] = '@telegram'
        
        if data['user']['email'] == '':
             data['user']['email'] = 'email@email.ru'
        
        data['nurse_info']['user'] = request.user.pk
        serializer = self.serializer_class(data=request.data['nurse_info'])
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_serializer = UserSerializer(request.user, data=request.data['user'])
        
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'user': user_serializer.data,
                'nurse_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )
    
    def get(self,request, format=None):
        info = self.getInfo(user=request.user)
        serializer = self.serializer_class(info)
        user_serializer = UserSerializer(request.user)

        return Response(
            {
                'user': user_serializer.data,
                'nurse_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )

    def put(self,request, format=None):
        info = self.getInfo(user=request.user)

        if request.data['user']['telegram_username'] == '':
             request.data['user']['telegram_username'] = '@telegram'
        
        if request.data['user']['email'] == '':
             request.data['user']['email'] = 'email@email.ru'

        

        serializer = self.serializer_class(info, data=request.data['nurse_info'])
        user_serializer = UserSerializer(request.user, data=request.data['user'])
        user_serializer.is_valid()
        serializer.is_valid()

        print(user_serializer.is_valid())
        if user_serializer.is_valid() and serializer.is_valid():
            user_serializer.save()
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'user': user_serializer.data,
                'nurse_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )
class NurseInfoDetail(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = NurseInfoSerializer


    def getInfo(self, user):
        try:
            return NurseInfo.objects.get(user__username=user)
        except NurseInfo.DoesNotExist:
            raise Http404("Нет такого пользователя")

  
    def get(self,request, tel, format=None):
        info = self.getInfo(user=tel)
        serializer = self.serializer_class(info)
        user = User.objects.get(username=tel)
        user_serializer = UserSerializer(user)

        return Response(
            {
                'user': user_serializer.data,
                'nurse_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )

    
# Пример body post запроса
# {
#     user:{
#         first_name:str,
#         last_name:str,
#         role:str,
# .       email:str,
#     }
#     customer_info:{
#          'region':str, 
#     }
# }

class CustomerInfoView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = CustomerInfoSerializer


    def getInfo(self, user):
        try:
            return CustomerInfo.objects.get(user=user)
        except CustomerInfo.DoesNotExist:
            raise Http404("Нет такого пользователя")

    def post(self, request):
        data = request.data

        data['customer_info']['user'] = request.user.pk
        if data['user']['telegram_username'] == '':
             data['user']['telegram_username'] = '@telegram'
        
        if data['user']['email'] == '':
             data['user']['email'] = 'email@email.ru'
        

        print(data, request.user)
        serializer = self.serializer_class(data=request.data['customer_info'])
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_serializer = UserSerializer(request.user, data=request.data['user'])
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'user': user_serializer.data,
                'customer_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )
    
    def get(self,request, format=None):
        info = self.getInfo(user=request.user)
        serializer = self.serializer_class(info)
        user_serializer = UserSerializer(request.user)

        return Response(
            {
                'user': user_serializer.data,
                'customer_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )

    def put(self,request, format=None):
        info = self.getInfo(user=request.user)
        serializer = self.serializer_class(info, data=request.data['customer_info'])
        user_serializer = UserSerializer(request.user, data=request.data['user'])
        print(request.data)
        user_serializer.is_valid()
        serializer.is_valid()
        if user_serializer.is_valid() and serializer.is_valid():
            user_serializer.save()
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'user': user_serializer.data,
                'customer_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )


class CustomerInfoDetail(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    serializer_class = CustomerInfoSerializer


    def getInfo(self, user):
        try:
            return CustomerInfo.objects.get(user__username=user)
        except CustomerInfo.DoesNotExist:
            raise Http404("Нет такого пользователя")

  
    def get(self,request, tel, format=None):
        info = self.getInfo(user=tel)
        serializer = self.serializer_class(info)
        user = User.objects.get(username=tel)
        user_serializer = UserSerializer(user)

        return Response(
            {
                'user': user_serializer.data,
                'customer_info': serializer.data
            }, 
            status=status.HTTP_200_OK
        )


#{
# action: 'delete'|'add'
# }

class SetLinkedCardView(APIView):
    authentication_classes = [authentication.TokenAuthentication] 
    def post(self,request, format=None):
        user = request.user
        user.linked_card = True if request.data['action'] == 'add' else False
        user.save()
        return Response(
            'ok', 
            status=status.HTTP_200_OK
        )

class ListenTgBot(APIView):
    permission_classes = [
        permissions.AllowAny,
    ]
    
    def post(self, request):
        print(request.data)
        return Response(
            'ok', 
            status=status.HTTP_200_OK
        )
