from .models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'projects_availables', 'projects_created']
        read_only_fields = ['username', 'token', 'card_type', 'card_mask', 'projects_availables','projects_created']
     

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.phone_number = validated_data.get('phone_number', instance.last_name)
        instance.save()
        return instance
