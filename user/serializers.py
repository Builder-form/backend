from .models import User, CustomerInfo, NurseInfo
from rest_framework import serializers


class CustomerInfoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomerInfo
        fields = ['user', 'region']
    
    def create(self, validated_data):
        return CustomerInfo.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.region = validated_data.get('region', instance.region)
        instance.save()
        return instance

class NurseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NurseInfo
        fields = ['user', 'age', 'citizenship', 'expirience', 'description']

    def create(self, validated_data):
        return  NurseInfo.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.age = validated_data.get('age', instance.age)
        instance.citizenship = validated_data.get('citizenship', instance.citizenship)
        instance.expirience = validated_data.get('expirience', instance.expirience)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','role', 'first_name', 'last_name', 'email', 'linked_card', 'token', 'telegram_username',]
        read_only_fields = ['username']

    def update(self, instance, validated_data):
        instance.role = validated_data.get('role', instance.role)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.telegram_username = validated_data.get('telegram_username', instance.telegram_username)
        # instance.chat_telegram_id = validated_data.get('chat_telegram_id', instance.chat_telegram_id)
        instance.save()
        return instance
