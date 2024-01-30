from django.urls import path

from .views import NurseApplicationView, \
    NurseApplicationDetail,  \
    NurseOrderView, \
    NurseOrderDetail,\
    NurseVisitView, \
    NurseVisitDetail, \
    NurseVisitsByOrder, \
    NurseAppelationView,\
    NurseAppelationsByVisit, \
    NurseAppelationDetail, \
    AcceptOrder, \
    MoveToArchiveOrder,\
    GetBalance,\
    GetVisitsByNurse,\
    CheckView, \
    PayView,\
    FailView


urlpatterns = [
    path('application/', NurseApplicationView.as_view(),),
    path('application/<str:id>/', NurseApplicationDetail.as_view()),
    path('order/', NurseOrderView.as_view(),),
    path('order/accept/<str:order_id>/', AcceptOrder.as_view()),
    path('order/to-archive/<str:order_id>/', MoveToArchiveOrder.as_view()),
    path('order/<str:id>/', NurseOrderDetail.as_view()),
    path('visit/', NurseVisitView.as_view(),),
    path('visit/nurse/',GetVisitsByNurse.as_view()),
    path('visit/order/<str:order_id>/', NurseVisitsByOrder.as_view()),
    path('visit/<str:visit_id>/', NurseVisitDetail.as_view()),
    path('appelation/', NurseAppelationView.as_view(),),
    path('appelation/visit/<str:visit_id>/', NurseAppelationsByVisit.as_view()),
    path('appelation/<str:appelation_id>/', NurseAppelationDetail.as_view()),
    path('balance/', GetBalance.as_view() ),
    path('notifications/check/', CheckView.as_view()),
    path('notifications/pay/', PayView.as_view()),
    path('notifications/fail/', FailView.as_view())
    
]