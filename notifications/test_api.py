from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from decimal import Decimal
from datetime import date, timedelta

from users.models import CustomUser
from jobs.models import Job
from proposals.models import Proposal
from contracts.models import Contract
from payments.models import Payment
from reviews.models import Review
from projects.models import Project
from notifications.utils import *


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_notifications(request):
    """
    API endpoint to test all notification types
    POST /api/test-notifications/
    """
    
    user = request.user
    results = []
    
    try:
        # Test 1: Create a test proposal notification
        if user.role == 'freelancer':
            # Find a job to propose to
            job = Job.objects.filter(user__role='client').first()
            if job:
                # Create test proposal notification for job owner
                notify_new_proposal_submitted_test(job.user, user, job)
                results.append("✓ New proposal notification sent")
        
        # Test 2: Create contract status change notification
        contract = Contract.objects.filter(
            models.Q(freelancer=user) | models.Q(client=user)
        ).first()
        
        if contract:
            notify_contract_status_change(contract, 'active', 'completed')
            results.append("✓ Contract status change notification sent")
        
        # Test 3: Create payment notification
        if user.role == 'freelancer':
            # Create test payment success notification
            create_and_send_notification(
                user=user,
                title="Payment Processed Successfully",
                message=f"Your payment of $500.00 has been processed successfully.",
                notification_type='payment',
                priority='high',
                action_url=f"/dashboard/payments",
                action_text="View Payments"
            )
            results.append("✓ Payment success notification sent")
        
        # Test 4: Create review notification
        create_and_send_notification(
            user=user,
            title="New Review Received",
            message=f"You received a 5-star review: 'Excellent work!'",
            notification_type='review',
            priority='medium',
            action_url=f"/dashboard/profile/reviews",
            action_text="View Review"
        )
        results.append("✓ Review notification sent")
        
        # Test 5: Create deadline approaching notification
        create_and_send_notification(
            user=user,
            title="Contract Deadline Approaching",
            message=f"Your contract deadline is in 2 days. Please ensure all deliverables are submitted on time.",
            notification_type='contract',
            priority='urgent',
            action_url=f"/dashboard/contracts",
            action_text="View Contract"
        )
        results.append("✓ Deadline notification sent")
        
        # Test 6: Create deliverable notification if user is client
        if user.role == 'client':
            create_and_send_notification(
                user=user,
                title="Deliverables Submitted",
                message=f"A freelancer has submitted deliverables for your contract. Please review and provide feedback.",
                notification_type='contract',
                priority='high',
                action_url=f"/dashboard/contracts",
                action_text="Review Deliverables"
            )
            results.append("✓ Deliverables notification sent")
        
        return Response({
            'success': True,
            'message': 'Test notifications sent successfully',
            'results': results
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error sending test notifications: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def notify_new_proposal_submitted_test(job_owner, freelancer, job):
    """Test version of proposal notification"""
    create_and_send_notification(
        user=job_owner,
        title="New Proposal Received",
        message=f"{freelancer.get_full_name() or freelancer.username} submitted a proposal for your job '{job.title}'",
        notification_type='proposal',
        priority='medium',
        action_url=f"/dashboard/jobs/{job.id}/proposals",
        action_text="View Proposal",
        data={
            'job_id': job.id,
            'freelancer_id': freelancer.id,
            'test': True
        }
    )
