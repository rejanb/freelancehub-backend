import stripe
from django.conf import settings
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from .models import Payment, PaymentAnalytics
from .serializers import (
    PaymentSerializer, CreatePaymentSerializer, PaymentAnalyticsSerializer,
    PaymentSummarySerializer, DashboardAnalyticsSerializer
)
from contracts.models import Contract
from projects.models import Project

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_dummy')

class PaymentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaymentPagination
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = Payment.objects.all()
        else:
            # Users can see payments where they are payer or recipient
            queryset = Payment.objects.filter(
                Q(payer=user) | Q(recipient=user)
            )
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        payment_type = self.request.query_params.get('type')
        contract_id = self.request.query_params.get('contract')
        project_id = self.request.query_params.get('project')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        return queryset.select_related(
            'payer', 'recipient', 'contract', 'project'
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePaymentSerializer
        return PaymentSerializer
    
    def perform_create(self, serializer):
        payment = serializer.save()
        
        # Update analytics for both users
        PaymentAnalytics.update_analytics(payment.payer)
        PaymentAnalytics.update_analytics(payment.recipient)
        
        return payment
    
    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """Get payments for current user with summary"""
        user = request.user
        
        # Get user's payments
        sent_payments = Payment.objects.filter(payer=user)
        received_payments = Payment.objects.filter(recipient=user)
        
        # Calculate summaries
        sent_summary = {
            'total_count': sent_payments.count(),
            'total_amount': sent_payments.aggregate(Sum('amount'))['amount__sum'] or 0,
            'pending_amount': sent_payments.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0,
            'completed_amount': sent_payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
        }
        
        received_summary = {
            'total_count': received_payments.count(),
            'total_amount': received_payments.aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
            'pending_amount': received_payments.filter(status='pending').aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
            'completed_amount': received_payments.filter(status='completed').aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
        }
        
        # Get recent payments
        all_payments = Payment.objects.filter(
            Q(payer=user) | Q(recipient=user)
        ).order_by('-created_at')[:10]
        
        return Response({
            'sent_payments': sent_summary,
            'received_payments': received_summary,
            'recent_payments': PaymentSerializer(all_payments, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get payment summary for current user"""
        user = request.user
        
        # Current month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_week = now - timedelta(days=now.weekday())
        
        if user.user_type == 'freelancer':
            payments = Payment.objects.filter(recipient=user)
            summary_data = {
                'total_payments': payments.count(),
                'total_amount': payments.filter(status='completed').aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
                'pending_payments': payments.filter(status='pending').count(),
                'pending_amount': payments.filter(status='pending').aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
                'completed_payments': payments.filter(status='completed').count(),
                'completed_amount': payments.filter(status='completed').aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
                'this_month_amount': payments.filter(
                    status='completed', processed_at__gte=start_of_month
                ).aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
                'this_week_amount': payments.filter(
                    status='completed', processed_at__gte=start_of_week
                ).aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
            }
        else:  # client
            payments = Payment.objects.filter(payer=user)
            summary_data = {
                'total_payments': payments.count(),
                'total_amount': payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
                'pending_payments': payments.filter(status='pending').count(),
                'pending_amount': payments.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0,
                'completed_payments': payments.filter(status='completed').count(),
                'completed_amount': payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
                'this_month_amount': payments.filter(
                    status='completed', processed_at__gte=start_of_month
                ).aggregate(Sum('amount'))['amount__sum'] or 0,
                'this_week_amount': payments.filter(
                    status='completed', processed_at__gte=start_of_week
                ).aggregate(Sum('amount'))['amount__sum'] or 0,
            }
        
        serializer = PaymentSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark payment as completed (admin only)"""
        payment = self.get_object()
        
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Only administrators can mark payments as completed'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payment.status = 'completed'
        payment.processed_at = timezone.now()
        payment.save()
        
        # Update analytics
        PaymentAnalytics.update_analytics(payment.payer)
        PaymentAnalytics.update_analytics(payment.recipient)
        
        return Response({'detail': 'Payment marked as completed'})

class CreatePaymentIntentView(APIView):
    """Create Stripe payment intent for processing payments"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            amount = request.data.get('amount')
            contract_id = request.data.get('contract_id')
            description = request.data.get('description', 'Project payment')
            
            if not amount or not contract_id:
                return Response(
                    {'error': 'Amount and contract_id are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate contract access
            try:
                contract = Contract.objects.get(id=contract_id)
                if request.user != contract.client and not request.user.is_superuser:
                    return Response(
                        {'error': 'Only the client can make payments for this contract'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Contract.DoesNotExist:
                return Response(
                    {'error': 'Contract not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'user_id': request.user.id,
                    'contract_id': contract_id,
                    'description': description
                }
            )
            
            # Create pending payment record
            payment = Payment.objects.create(
                contract=contract,
                project=contract.project_proposal.project,
                payer=request.user,
                recipient=contract.freelancer,
                amount=amount,
                description=description,
                status='pending',
                stripe_payment_intent_id=intent['id'],
                platform_fee=float(amount) * 0.05,  # 5% platform fee
            )
            
            return Response({
                'client_secret': intent['client_secret'],
                'payment_id': payment.id
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentAnalyticsView(APIView):
    """Get comprehensive payment analytics for current user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Update analytics first
        analytics = PaymentAnalytics.update_analytics(user)
        
        # Get monthly trends (last 6 months)
        monthly_trends = self.get_monthly_trends(user)
        
        # Get payment breakdown by type
        payment_breakdown = self.get_payment_breakdown(user)
        
        # Get recent payments
        recent_payments = Payment.objects.filter(
            Q(payer=user) | Q(recipient=user)
        ).order_by('-created_at')[:5]
        
        dashboard_data = {
            'user_type': user.user_type,
            'total_earned': analytics.total_earned if user.user_type == 'freelancer' else 0,
            'total_spent': analytics.total_spent if user.user_type == 'client' else 0,
            'pending_payments': analytics.total_pending_payments,
            'current_month_earned': analytics.current_month_earned,
            'current_month_spent': analytics.current_month_spent,
            'completed_projects': analytics.completed_projects_count,
            'pending_projects': analytics.pending_projects_count,
            'available_projects': analytics.available_projects_count,
            'recent_payments': PaymentSerializer(recent_payments, many=True).data,
            'payment_breakdown': payment_breakdown,
            'monthly_trends': monthly_trends,
        }
        
        serializer = DashboardAnalyticsSerializer(dashboard_data)
        return Response(serializer.data)
    
    def get_monthly_trends(self, user):
        """Get payment trends for last 6 months"""
        trends = []
        now = timezone.now()
        
        for i in range(6):
            month_start = (now.replace(day=1) - timedelta(days=32*i)).replace(day=1)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            if user.user_type == 'freelancer':
                amount = Payment.objects.filter(
                    recipient=user,
                    status='completed',
                    processed_at__range=[month_start, month_end]
                ).aggregate(Sum('net_amount'))['net_amount__sum'] or 0
            else:
                amount = Payment.objects.filter(
                    payer=user,
                    status='completed',
                    processed_at__range=[month_start, month_end]
                ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            trends.append({
                'month': month_start.strftime('%Y-%m'),
                'amount': float(amount),
                'label': month_start.strftime('%B %Y')
            })
        
        return list(reversed(trends))
    
    def get_payment_breakdown(self, user):
        """Get payment breakdown by type"""
        if user.user_type == 'freelancer':
            payments = Payment.objects.filter(recipient=user, status='completed')
        else:
            payments = Payment.objects.filter(payer=user, status='completed')
        
        breakdown = {}
        for payment_type, label in Payment.PAYMENT_TYPE_CHOICES:
            count = payments.filter(payment_type=payment_type).count()
            if count > 0:
                if user.user_type == 'freelancer':
                    amount = payments.filter(payment_type=payment_type).aggregate(
                        Sum('net_amount')
                    )['net_amount__sum'] or 0
                else:
                    amount = payments.filter(payment_type=payment_type).aggregate(
                        Sum('amount')
                    )['amount__sum'] or 0
                
                breakdown[payment_type] = {
                    'label': label,
                    'count': count,
                    'amount': float(amount)
                }
        
        return breakdown

class PaymentWebhookView(APIView):
    """Handle Stripe webhook events"""
    permission_classes = []  # Public endpoint
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            return Response({'error': 'Invalid signature'}, status=400)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self.handle_payment_success(payment_intent)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            self.handle_payment_failure(payment_intent)
        
        return Response({'status': 'success'})
    
    def handle_payment_success(self, payment_intent):
        """Handle successful payment"""
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'completed'
            payment.processed_at = timezone.now()
            payment.transaction_id = payment_intent.get('charges', {}).get('data', [{}])[0].get('id')
            payment.save()
            
            # Update analytics
            PaymentAnalytics.update_analytics(payment.payer)
            PaymentAnalytics.update_analytics(payment.recipient)
            
        except Payment.DoesNotExist:
            pass  # Payment not found
    
    def handle_payment_failure(self, payment_intent):
        """Handle failed payment"""
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'failed'
            payment.save()
            
        except Payment.DoesNotExist:
            pass  # Payment not found