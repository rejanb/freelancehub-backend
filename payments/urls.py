from django.urls import path
from .views import CreatePaymentIntentView, PaymentListView, PaymentDetailView  

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('my-payments/', PaymentListView.as_view(), name='my-payments'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
]
