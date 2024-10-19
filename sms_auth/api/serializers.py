from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

User = get_user_model()

class EntrySerializer(serializers.Serializer):
    email = serializers.EmailField()


class AuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.IntegerField()


class ChangePhoneNumberSerializer(serializers.Serializer):
    new_email = serializers.EmailField()


class DefaultUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'jwt_token'
        ]