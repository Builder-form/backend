from django.urls import path

from .views import NurseInfoView, CustomerInfoView, UserView, CustomerInfoDetail, NurseInfoDetail,  SetLinkedCardView, ListenTgBot, UserMeView


urlpatterns = [
    path('user_self_info/', UserMeView.as_view()),
    path('user_info/<str:tel>/', UserView.as_view()),
    path('nurse_info/', NurseInfoView.as_view()),
    path('customer_info/', CustomerInfoView.as_view()),
    path('nurse_info/<str:tel>/',NurseInfoDetail.as_view()),
    path('customer_info/<str:tel>/',CustomerInfoDetail.as_view()),
    path('set_linked_card/', SetLinkedCardView.as_view()),
    path('listen_bot/', ListenTgBot.as_view())
]