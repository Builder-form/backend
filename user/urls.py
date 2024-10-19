from django.urls import path

from .views import UserView, UserMeView


urlpatterns = [
    path('user_self_info/', UserMeView.as_view()),
    path('user_info/<str:tel>/', UserView.as_view()),
]

