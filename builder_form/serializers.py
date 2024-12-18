from .models import Answer, AnswerQuestion, Question, QuestionInstance, Project, Termin
from rest_framework import serializers
from user.models import User
import datetime


class QuestionInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionInstance
        read_only_fields = ['project', 'pk',]
        fields = ['qid','project','params', 'parent', 'text', 'pk']
    
    def create(self, validated_data):
        return QuestionInstance.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.params = validated_data.get('params', instance.params)
        instance.parent = validated_data.get('parent', instance.parent)
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance


class TerminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Termin
        read_only_fields = ['termin', 'qid', 'description']
        fields = ['termin', 'qid', 'description']
    
    def create(self, validated_data):
        return Termin.objects.create(**validated_data)

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        read_only_fields = ['text', 'id', 'type']
        fields = ['text', 'id', 'type']
    
    def create(self, validated_data):
        return Answer.objects.create(**validated_data)

class AnswerQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerQuestion
        read_only_fields = ['answer', 'project', 'question_instance']
        fields = ['answer_text','project', 'answer', 'question_instance']
    
    def create(self, validated_data):
        return AnswerQuestion.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.answer_text = validated_data.get('answer_text', instance.answer_text)
        instance.save()
        return instance

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'id', 'last_edit', 'created', 'progress', 'user', 'tree']
        read_only_fields = ['id', 'last_edit','created','progress', 'tree']
   
    def create(self, validated_data):
        return Project.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
    
class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'last_edit', 'created', 'progress', 'user']
        read_only_fields = ['id', 'last_edit','created','progress', 'user']