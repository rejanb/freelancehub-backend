from django.urls import path
from .views import CreatePaymentIntentView, PaymentListView

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('my-payments/', PaymentListView.as_view(), name='my-payments'),
]