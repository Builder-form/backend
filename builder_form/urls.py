from django.urls import path
from .views import AnswerQuestionAPIView,GetCurrentQuestionAPIView, GetProjectsAPIView, ProjectAPIView, CreateProjectAPIView, GetAnswersAPIView,BackProjectAPIView


urlpatterns = [
    path("answer_question/", AnswerQuestionAPIView.as_view()),
    path("current_question/", GetCurrentQuestionAPIView.as_view()),
    path("get_projects/", GetProjectsAPIView.as_view()),
    path("get_answers/", GetAnswersAPIView.as_view()),
    path("project/", CreateProjectAPIView.as_view()),
    path('project/back/', BackProjectAPIView.as_view()),
    path("project/<str:id>/", ProjectAPIView.as_view()),

]