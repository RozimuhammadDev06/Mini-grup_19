from django.urls import path
from apps.payment.views import (
    PrepareCallbackView, CompleteCallbackView,
    CheckoutPayView, CardRequestView, CardVerifyView
)

urlpatterns = [
    path('prepare/', PrepareCallbackView.as_view(), name='payment-prepare'),
    path('complete/', CompleteCallbackView.as_view(), name='payment-complete'),
    path('checkout/orders/<int:order_id>/pay/', CheckoutPayView.as_view(), name='checkout-pay'),
    path('card/request/', CardRequestView.as_view(), name='card-request'),
    path('card/verify/', CardVerifyView.as_view(), name='card-verify'),
]