from django.contrib import admin
from .models import Question, Answer, AnswerQuestion, Project, QuestionInstance, Termin


class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ('text', 'id', 'type')
    extra = 0

# Register your models here.
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id', 'text_template')
    inlines = [AnswerInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id', 'text', 'type')


@admin.register(QuestionInstance)
class QuestionInstanceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'qid', 'text', 'params')



@admin.register(Termin)
class TerminAdmin(admin.ModelAdmin):
    list_display = ('pk', 'qid', 'termin', 'description')

@admin.register(AnswerQuestion)
class QuestionInstanceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'answer', 'answer_text')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = ('name', 'id','questions_queue','history_queue','last_edit', 'created', 'user')
    list_display = ('name','id', 'created','last_edit')
    readonly_fields = ('id', 'last_edit', 'created', 'history_queue')

