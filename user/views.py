from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions, status
from .models import User
from .serializers import  UserSerializer
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
    
    def put(self, request, format=None):
        serializer = self.serializer_class(request.user, data=request.data)

        if serializer.is_valid():
            serializer.save()
        else:
            return Response(
            request.data, 
            status=status.HTTP_400_BAD_REQUEST
        ) 

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
        except:
            raise Http404("Нет такого пользователя")

    def get(self,request, tel, format=None):
        info = self.getInfo(user=tel)
        serializer = self.serializer_class(info)

        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
        )