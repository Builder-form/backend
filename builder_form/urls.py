from django.urls import path
from .views import AnswerQuestionAPIView, CreatePaymentView, ExecutePaymentView,GetCurrentQuestionAPIView, GetProjectsAPIView, ProjectAPIView, CreateProjectAPIView, GetAnswersAPIView,BackProjectAPIView, ProjectUserAPIView, SendEmailView, TestEmailView, TransactionAPIView, GetAnswersForBuilderAPIView

urlpatterns = [
    path("answer_question/", AnswerQuestionAPIView.as_view()),
    path("current_question/", GetCurrentQuestionAPIView.as_view()),
    path("get_projects/", GetProjectsAPIView.as_view()),
    path("get_answers/", GetAnswersAPIView.as_view()),
    path("get_answers_for_builder/", GetAnswersForBuilderAPIView.as_view()),
    # path("project/", CreateProjectAPIView.as_view()),
    path('project/back/', BackProjectAPIView.as_view()),
    path("project/<str:id>/", ProjectAPIView.as_view()),
    path('create_payment/', CreatePaymentView.as_view()),
    path('execute_payment/', ExecutePaymentView.as_view()),
    path('user_projects/', ProjectUserAPIView.as_view()),
    path('send_email/', SendEmailView.as_view()),
    path('user_transactions/', TransactionAPIView.as_view()),
]