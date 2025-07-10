import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework import generics
from .models import Payment
from .serializers import PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        contract_id = request.data.get('contract_id')
        if not amount or not contract_id:
            return Response({'error': 'Amount and contract_id are required'}, status=400)
        intent = stripe.PaymentIntent.create(
            amount=int(float(amount) * 100),
            currency='usd',
            metadata={'user_id': request.user.id, 'contract_id': contract_id}
        )
        # Create a pending Payment record
        Payment.objects.create(
            contract_id=contract_id,
            user=request.user,
            amount=amount,
            status='pending',
            transaction_id=intent['id']
        )
        return Response({'clientSecret': intent['client_secret']})

class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)