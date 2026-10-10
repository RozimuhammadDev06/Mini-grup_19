from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login),
    path('register/', views.register),
    path('pay/init/', views.PayInitView.as_view()),
    path('card/request/', views.CardRequestView.as_view()),
    path('card/verify/', views.CardVerifyView.as_view()),
    path('card/payment/', views.CardPaymentView.as_view()),
    path('prepare/', views.PrepareCallbackView.as_view()),
    path('complete/', views.CompleteCallbackView.as_view()),
]