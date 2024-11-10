from django.contrib import admin
from .models import APPSettings, Question, Answer, AnswerQuestion, Project, QuestionInstance, Termin, NamingCondition


class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ('text', 'id', 'type')
    extra = 0

class NamingConditionInline(admin.TabularInline):
    model = NamingCondition
    fields = ('left_operand', 'condition_type', 'right_operand', 'text_template')
    raw_id_fields = ('right_operand',)
    extra = 0
    fk_name = "parent_question"


admin.site.register(NamingCondition)
@admin.register(APPSettings)
class APPSettingsAdmin(admin.ModelAdmin):
    list_display = ('isActive', 'cost', 'projects_per_purchase')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id', 'text_template')
    inlines = [AnswerInline, NamingConditionInline]

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id', 'text', 'type')
    search_fields = ('pk', 'id', 'text', 'type')
    list_filter = ('type',)

@admin.register(QuestionInstance)
class QuestionInstanceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'qid', 'text', 'params', 'context')
    search_fields = ('pk', 'qid', 'text', 'params')




@admin.register(Termin)
class TerminAdmin(admin.ModelAdmin):
    list_display = ('pk', 'qid', 'termin', 'description')

@admin.register(AnswerQuestion)
class AnswerQuestionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'answer', 'answer_text', )
    search_fields =  ('pk', 'answer', 'answer_text')



@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = ('name', 'id','questions_queue','history_queue','last_edit', 'created', 'user')
    list_display = ('name','id', 'created','last_edit')
    readonly_fields = ('id', 'last_edit', 'created', 'history_queue')

