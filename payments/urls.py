from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet, CreatePaymentIntentView, PaymentAnalyticsView, PaymentWebhookView
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('analytics/', PaymentAnalyticsView.as_view(), name='payment-analytics'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),
]