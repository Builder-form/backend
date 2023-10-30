from django.urls import path

from .views import NurseInfoView, CustomerInfoView, UserView, CustomerInfoDetail, NurseInfoDetail,  SetLinkedCardView


urlpatterns = [
    path('user_info/', UserView.as_view()),
    path('nurse_info/', NurseInfoView.as_view()),
    path('customer_info/', CustomerInfoView.as_view()),
    path('nurse_info/<str:tel>/',NurseInfoDetail.as_view()),
    path('customer_info/<str:tel>/',CustomerInfoDetail.as_view()),
    path('set_linked_card/', SetLinkedCardView.as_view())
]