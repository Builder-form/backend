from django.utils.module_loading import import_string

from rest_framework import generics, permissions

from ..conf import conf
from ..services import AuthService, GeneratorService
from .mixins import ResponsesMixin
from .serializers import \
    AuthSerializer, \
    EntrySerializer, \
    ChangePhoneNumberSerializer, \
    DefaultUserSerializer


class EntryAPIView(ResponsesMixin, generics.GenericAPIView):
    """
    Single endpoint to sign-in/sign-up
    :param
        - phone_number
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    serializer_class = EntrySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            GeneratorService.execute(email=email)
            return self.simple_text_response()
        else:
            return self.error_response(serializer.errors)


class AuthAPIView(ResponsesMixin, generics.GenericAPIView):
    """
    Single endpoint to auth thgrough phone_number + code
        params:
         - phone_number
         - code
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    serializer_class = AuthSerializer

    def get_response_serializer(self):
        try:
            serializer = import_string(conf.SMS_USER_SERIALIZER)
        except ImportError:
            serializer = DefaultUserSerializer

        return serializer

    def after_auth(self, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            code = serializer.validated_data.get("code")
            user, is_created = AuthService.execute(email=email, code=code)
            self.after_auth(user=user, is_created=is_created)
            serializer = self.get_response_serializer()
            success_value = serializer(instance=user, context={'request': request}).data
            return self.success_objects_response(success_value)
        else:
            return self.error_response(serializer.errors)


class ChangePhoneNumberAPIView(ResponsesMixin, generics.GenericAPIView):
    serializer_class = ChangePhoneNumberSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_email = serializer.validated_data.get('new_email')
            owner = request.user
            GeneratorService.execute(email=new_email, owner=owner)

            return self.simple_text_response()

        else:
            return self.error_response(serializer.errors)
