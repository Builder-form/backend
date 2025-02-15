from django.contrib import admin
from .models import APPSettings, Question, Answer, AnswerQuestion, Project, QuestionInstance, Termin, NamingCondition, EmailMessage, Transaction
from django.core.mail import EmailMessage as DjangoEmailMessage
from django.conf import settings


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
    search_fields =  ('pk', 'name', 'user__username')
    ordering = ('-created', '-last_edit'
                )
    fields = ('name', 'id','questions_queue','history_queue','last_edit', 'created', 'user', 'short_description')
    list_display = ('name','id', 'created','last_edit')
    readonly_fields = ('id', 'last_edit', 'created', 'history_queue', 'short_description')

@admin.register(EmailMessage)
class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created')
    filter_horizontal = ('users', 'groups')
    actions = ['send_emails']

    def send_emails(self, request, queryset):
        for email_campaign in queryset:
            recipients = set()
            for user in email_campaign.users.all():
                if user.username:
                    recipients.add(user.username)
            for group in email_campaign.groups.all():
                for user in group.user_set.all():
                    if user.username:
                        recipients.add(user.username)
            print(recipients)
            recipients = list(recipients)
            if recipients:
                django_email = DjangoEmailMessage(
                    subject=email_campaign.subject,
                    body=email_campaign.html_content,
                    from_email=settings.EMAIL_HOST_USER,
                    to=recipients,
                )
                django_email.content_subtype = 'html'
                print(django_email)
                django_email.send()
        self.message_user(request, "Emails sent successfully")
    send_emails.short_description = "Send selected emails"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'created', 'amount', 'project')
    search_fields = ('pk', 'created', 'amount', 'project__name')
    list_filter = ('project__name',)

