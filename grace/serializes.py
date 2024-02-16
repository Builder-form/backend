from .models import Wallet, TransferPrefs, NurseApplication, NurseOrder, NurseVisit, NurseAppelation
from rest_framework import serializers
from user.models import User
import datetime

class NurseApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = NurseApplication

        fields = ['user', 'care_type', 'time_start', 'contact_type', 'id', 'active']
        read_only_fields = ['id']

    def create(self, validated_data):
        return NurseApplication.objects.create(
            **validated_data
        )
    
    def update(self, instance, validated_data):
        instance.care_type = validated_data.get('care_type', instance.care_type)
        instance.time_start = validated_data.get('time_start', instance.time_start)
        instance.contact_type = validated_data.get('contact_type', instance.contact_type )
        instance.save()
        return instance

class NurseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = NurseOrder
        fields = ['id', 'application', 'care_type', 'status','nurse', 'address', 'cost', 'comment', 'client', 'cost_per_week', 'order_number']
        read_only_fields = ['id', 'client', 'cost_per_week', 'order_number' ]

    def create(self, validated_data):
        return NurseOrder.objects.create(**validated_data)
        
    def update(self, instance, validated_data):
        instance.nurse = validated_data.get('nurse', instance.nurse)
        instance.address = validated_data.get('address', instance.address)
        instance.cost = validated_data.get('cost', instance.cost)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.save()
        return instance


class NurseVisitSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = NurseVisit
        read_only_fields = ['id', 'create_date', 'completed_date',  'appelations']
        fields = [ 'completed_date', 'id', 'create_date', 'order', 'date', 'time_start', 'time_end', 'completed', 'nursecomment',  'appelations']
    
    def create(self, validated_data):
        return NurseVisit.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.completed = validated_data.get('completed', instance.completed)
        instance.completed_date =  datetime.datetime.now()
        instance.nursecomment = validated_data.get('nursecomment', instance.nursecomment)
        instance.save()
        return instance

class NurseAppelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NurseAppelation
        read_only_fields = ['id']
        fields = ['id','visit', 'comment', 'status', 'ans']
    
    def create(self, validated_data):
        return NurseAppelation.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.comment = validated_data.get('comment', instance.сomment)
        instance.status = validated_data.get('status', instance.status)
        instance.ans = validated_data.get('ans', instance.ans)
        instance.save()
        return instance
