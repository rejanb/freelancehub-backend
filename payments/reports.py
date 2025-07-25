from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Payment
from contracts.models import Contract
from users.models import CustomUser

class PaymentStatsView(APIView):
    """
    Minimal payment reporting for dev/testing
    Returns basic stats for Client, Freelancer, and Admin roles
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.user_type == 'admin':
            return self.get_admin_stats()
        elif user.user_type == 'client':
            return self.get_client_stats(user)
        elif user.user_type == 'freelancer':
            return self.get_freelancer_stats(user)
        else:
            return Response({'error': 'Invalid user type'}, status=400)
    
    def get_admin_stats(self):
        """Admin dashboard stats"""
        # Get date ranges
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        # Basic platform stats
        total_payments = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        recent_payments = Payment.objects.filter(
            status='completed',
            created_at__date__gte=last_30_days
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Platform revenue (assuming 5% fee)
        platform_revenue = (total_payments['total'] or 0) * 0.05
        
        # Active contracts
        active_contracts = Contract.objects.filter(status='active').count()
        
        return Response({
            'role': 'admin',
            'platform_stats': {
                'total_payments': {
                    'amount': total_payments['total'] or 0,
                    'count': total_payments['count']
                },
                'last_30_days': {
                    'amount': recent_payments['total'] or 0,
                    'count': recent_payments['count']
                },
                'platform_revenue': platform_revenue,
                'active_contracts': active_contracts,
                'total_users': CustomUser.objects.count()
            }
        })
    
    def get_client_stats(self, user):
        """Client spending stats"""
        # Client's payments (money spent)
        total_spent = Payment.objects.filter(
            user=user,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        pending_payments = Payment.objects.filter(
            user=user,
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent activity
        recent_payments = Payment.objects.filter(
            user=user,
            status='completed',
            created_at__date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        # Active contracts
        active_contracts = Contract.objects.filter(
            proposal__job__user=user,
            status='active'
        ).count()
        
        return Response({
            'role': 'client',
            'spending_stats': {
                'total_spent': total_spent,
                'pending_payments': pending_payments,
                'recent_payments_count': recent_payments,
                'active_contracts': active_contracts
            }
        })
    
    def get_freelancer_stats(self, user):
        """Freelancer earnings stats"""
        # Freelancer's earnings (money received)
        # Note: In a real system, you'd track payee separately
        total_earned = Payment.objects.filter(
            contract__proposal__user=user,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        pending_earnings = Payment.objects.filter(
            contract__proposal__user=user,
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent activity
        recent_payments = Payment.objects.filter(
            contract__proposal__user=user,
            status='completed',
            created_at__date__gte=timezone.now().date() - timedelta(days=30)
        ).count()
        
        # Active contracts
        active_contracts = Contract.objects.filter(
            proposal__user=user,
            status='active'
        ).count()
        
        return Response({
            'role': 'freelancer',
            'earnings_stats': {
                'total_earned': total_earned,
                'pending_earnings': pending_earnings,
                'recent_payments_count': recent_payments,
                'active_contracts': active_contracts
            }
        })


class QuickPaymentView(APIView):
    """
    Minimal payment processing for dev/testing
    Simplified payment creation
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        amount = request.data.get('amount', 0)
        contract_id = request.data.get('contract_id')
        description = request.data.get('description', 'Test payment')
        
        if not amount or amount <= 0:
            return Response({'error': 'Valid amount required'}, status=400)
        
        try:
            # Create a test payment (simplified)
            payment = Payment.objects.create(
                contract_id=contract_id,
                user=request.user,
                amount=amount,
                status='pending',
                transaction_id=f'test_{timezone.now().timestamp()}'
            )
            
            return Response({
                'payment_id': payment.id,
                'amount': payment.amount,
                'status': payment.status,
                'message': 'Test payment created successfully'
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)
