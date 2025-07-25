from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from .serializers import NotificationSerializer
import json


def send_notification_to_user(user_id, notification_data):
    """
    Send a real-time notification to a specific user via WebSocket
    """
    channel_layer = get_channel_layer()
    group_name = f'notifications_{user_id}'
    
    # Send via WebSocket
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_message',
            'message': notification_data
        }
    )


def create_and_send_notification(user, title, message, notification_type='info', data=None):
    """
    Create a notification in the database and send it via WebSocket
    
    Args:
        user: User instance to send notification to
        title (str): Notification title
        message (str): Notification message  
        notification_type (str): Type of notification ('info', 'success', 'warning', 'error')
        data (dict): Additional data to include
    
    Returns:
        Notification: The created notification instance
    """
    # Create notification in database
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data or {}
    )
    
    # Send real-time notification via WebSocket
    try:
        send_notification_to_user(
            user_id=user.id,
            notification_data={
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'data': notification.data
            }
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send real-time notification: {e}")
    
    return notification


def send_notification_to_group(group_name, notification_data):
    """
    Send a notification to a group of users via WebSocket
    
    Args:
        group_name (str): The name of the group to send notification to
        notification_data (dict): The notification data to send
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_message', 
            'message': notification_data
        }
    )


# Notification types
NOTIFICATION_TYPES = {
    'PROJECT_CREATED': 'project_created',
    'PROPOSAL_RECEIVED': 'proposal_received',
    'PROPOSAL_ACCEPTED': 'proposal_accepted',
    'PROPOSAL_REJECTED': 'proposal_rejected',
    'CONTRACT_CREATED': 'contract_created',
    'CONTRACT_COMPLETED': 'contract_completed',
    'PAYMENT_RECEIVED': 'payment_received',
    'MESSAGE_RECEIVED': 'message_received',
}


# Quick notification functions for common use cases
def notify_proposal_received(client_user, project, freelancer):
    """Send notification when a new proposal is received"""
    return create_and_send_notification(
        user=client_user,
        title="New Proposal Received",
        message=f"You received a new proposal from {freelancer.get_full_name() or freelancer.username} for '{project.title}'",
        notification_type='info',
        data={
            'project_id': project.id,
            'freelancer_id': freelancer.id,
            'type': NOTIFICATION_TYPES['PROPOSAL_RECEIVED']
        }
    )


def notify_proposal_accepted(freelancer_user, project):
    """Send notification when a proposal is accepted"""
    return create_and_send_notification(
        user=freelancer_user,
        title="Proposal Accepted! 🎉",
        message=f"Your proposal for '{project.title}' has been accepted!",
        notification_type='success',
        data={
            'project_id': project.id,
            'type': NOTIFICATION_TYPES['PROPOSAL_ACCEPTED']
        }
    )


def notify_proposal_rejected(freelancer_user, project):
    """Send notification when a proposal is rejected"""
    return create_and_send_notification(
        user=freelancer_user,
        title="Proposal Update",
        message=f"Your proposal for '{project.title}' was not selected this time.",
        notification_type='warning',
        data={
            'project_id': project.id,
            'type': NOTIFICATION_TYPES['PROPOSAL_REJECTED']
        }
    )


def notify_contract_created(freelancer_user, contract):
    """Send notification when a contract is created"""
    return create_and_send_notification(
        user=freelancer_user,
        title="Contract Created 📋",
        message=f"A new contract has been created for '{contract.project_proposal.project.title}'",
        notification_type='success',
        data={
            'contract_id': contract.id,
            'project_id': contract.project_proposal.project.id,
            'type': NOTIFICATION_TYPES['CONTRACT_CREATED']
        }
    )


def notify_payment_received(user, amount, project):
    """Send notification when payment is received"""
    return create_and_send_notification(
        user=user,
        title="Payment Received 💰",
        message=f"You received ${amount} payment for '{project.title}'",
        notification_type='success',
        data={
            'amount': str(amount),
            'project_id': project.id,
            'type': NOTIFICATION_TYPES['PAYMENT_RECEIVED']
        }
    )


def create_and_send_notification(user, title='', message='', notification_type='info', 
                                priority='medium', action_url=None, action_text=None,
                                data=None, content_object=None):
    """
    Create a notification in the database and send it via WebSocket
    """
    if data is None:
        data = {}
    
    # Create notification in database
    notification = Notification.objects.create(
        user=user,
        title=title or 'New Notification',
        message=message,
        notification_type=notification_type,
        priority=priority,
        action_url=action_url,
        action_text=action_text,
        data=data,
        content_object=content_object
    )
    
    # Serialize notification data
    serializer = NotificationSerializer(notification)
    notification_data = {
        'type': 'notification',
        'data': serializer.data
    }
    
    # Send via WebSocket
    send_notification_to_user(user.id, notification_data)
    
    return notification


def send_bulk_notification(user_ids, title='', message='', notification_type='info', priority='medium'):
    """
    Send notifications to multiple users
    """
    notifications = []
    
    for user_id in user_ids:
        from users.models import CustomUser
        try:
            user = CustomUser.objects.get(id=user_id)
            notification = create_and_send_notification(
                user=user, 
                title=title, 
                message=message, 
                notification_type=notification_type,
                priority=priority
            )
            notifications.append(notification)
        except CustomUser.DoesNotExist:
            continue
    
    return notifications


def create_job_notification(user, job, action_type):
    """Create job-related notifications"""
    title_map = {
        'created': f'New job posted: {job.title}',
        'applied': f'New application for: {job.title}',
        'updated': f'Job updated: {job.title}',
        'closed': f'Job closed: {job.title}',
    }
    
    return create_and_send_notification(
        user=user,
        title=title_map.get(action_type, f'Job {action_type}: {job.title}'),
        message=f'Job: {job.title}',
        notification_type='job',
        action_url=f'/dashboard/jobs/{job.id}',
        data={'job_id': job.id, 'action': action_type}
    )


def create_payment_notification(user, payment, action_type):
    """Create payment-related notifications"""
    title_map = {
        'received': f'Payment received: ${payment.amount}',
        'sent': f'Payment sent: ${payment.amount}',
        'pending': f'Payment pending: ${payment.amount}',
        'failed': f'Payment failed: ${payment.amount}',
    }
    
    return create_and_send_notification(
        user=user,
        title=title_map.get(action_type, f'Payment {action_type}: ${payment.amount}'),
        message=f'Payment of ${payment.amount}',
        notification_type='payment',
        priority='high' if action_type == 'failed' else 'medium',
        action_url=f'/dashboard/payments/{payment.id}',
        data={'payment_id': payment.id, 'amount': str(payment.amount), 'action': action_type}
    )


# ============ SPECIFIC NOTIFICATION TRIGGERS ============

def notify_new_proposal_submitted(proposal):
    """
    Notify job owner when a new proposal is submitted
    """
    job_owner = proposal.job.user
    freelancer = proposal.user
    
    create_and_send_notification(
        user=job_owner,
        title="New Proposal Received",
        message=f"{freelancer.get_full_name() or freelancer.username} submitted a proposal for your job '{proposal.job.title}'",
        notification_type='proposal',
        priority='medium',
        action_url=f"/dashboard/jobs/{proposal.job.id}/proposals",
        action_text="View Proposal",
        data={
            'proposal_id': proposal.id,
            'job_id': proposal.job.id,
            'freelancer_id': freelancer.id,
            'proposal_amount': str(proposal.budget) if hasattr(proposal, 'budget') else None
        },
        content_object=proposal
    )


def notify_proposal_accepted_contract_created(contract):
    """
    Notify freelancer when their proposal is accepted and contract is created
    """
    freelancer = contract.freelancer
    client = contract.client
    
    create_and_send_notification(
        user=freelancer,
        title="Proposal Accepted - Contract Created!",
        message=f"Great news! {client.get_full_name() or client.username} accepted your proposal. A new contract has been created.",
        notification_type='contract',
        priority='high',
        action_url=f"/dashboard/contracts/{contract.id}",
        action_text="View Contract",
        data={
            'contract_id': contract.id,
            'client_id': client.id,
            'contract_amount': str(contract.amount) if hasattr(contract, 'amount') else None
        },
        content_object=contract
    )


def notify_contract_status_change(contract, old_status, new_status):
    """
    Notify both parties when contract status changes
    """
    users_to_notify = [contract.client, contract.freelancer]
    
    status_messages = {
        'active': 'Contract has been activated and work can begin',
        'completed': 'Contract has been marked as completed',
        'cancelled': 'Contract has been cancelled',
        'disputed': 'Contract is under dispute review',
        'paused': 'Contract has been paused'
    }
    
    for user in users_to_notify:
        is_client = user == contract.client
        other_party = contract.freelancer if is_client else contract.client
        
        create_and_send_notification(
            user=user,
            title=f"Contract Status Updated",
            message=f"Contract with {other_party.get_full_name() or other_party.username} status changed from {old_status} to {new_status}. {status_messages.get(new_status, '')}",
            notification_type='contract',
            priority='high' if new_status in ['cancelled', 'disputed'] else 'medium',
            action_url=f"/dashboard/contracts/{contract.id}",
            action_text="View Contract",
            data={
                'contract_id': contract.id,
                'old_status': old_status,
                'new_status': new_status,
                'other_party_id': other_party.id
            },
            content_object=contract
        )


def notify_contract_deadline_approaching(contract, days_remaining):
    """
    Notify both parties when contract deadline is approaching
    """
    users_to_notify = [contract.client, contract.freelancer]
    
    urgency = 'urgent' if days_remaining <= 1 else 'high' if days_remaining <= 3 else 'medium'
    
    for user in users_to_notify:
        is_client = user == contract.client
        role = "client" if is_client else "freelancer"
        
        create_and_send_notification(
            user=user,
            title=f"Contract Deadline Approaching",
            message=f"Your contract deadline is in {days_remaining} day{'s' if days_remaining != 1 else ''}. Please ensure all deliverables are submitted on time.",
            notification_type='contract',
            priority=urgency,
            action_url=f"/dashboard/contracts/{contract.id}",
            action_text="View Contract",
            data={
                'contract_id': contract.id,
                'days_remaining': days_remaining,
                'deadline': contract.deadline.isoformat() if hasattr(contract, 'deadline') and contract.deadline else None
            },
            content_object=contract
        )


def notify_deliverables_submitted(contract, deliverable=None):
    """
    Notify client when freelancer submits deliverables
    """
    client = contract.client
    freelancer = contract.freelancer
    
    create_and_send_notification(
        user=client,
        title="Deliverables Submitted",
        message=f"{freelancer.get_full_name() or freelancer.username} has submitted deliverables for your contract. Please review and provide feedback.",
        notification_type='contract',
        priority='high',
        action_url=f"/dashboard/contracts/{contract.id}/deliverables",
        action_text="Review Deliverables",
        data={
            'contract_id': contract.id,
            'freelancer_id': freelancer.id,
            'deliverable_id': deliverable.id if deliverable else None
        },
        content_object=deliverable or contract
    )


def notify_payment_processed_successfully(payment):
    """
    Notify freelancer when payment is processed successfully
    """
    freelancer = payment.freelancer if hasattr(payment, 'freelancer') else payment.recipient
    
    create_and_send_notification(
        user=freelancer,
        title="Payment Processed Successfully",
        message=f"Great news! Your payment of ${payment.amount} has been processed successfully.",
        notification_type='payment',
        priority='high',
        action_url=f"/dashboard/payments/{payment.id}",
        action_text="View Payment",
        data={
            'payment_id': payment.id,
            'amount': str(payment.amount),
            'payment_method': getattr(payment, 'payment_method', None),
            'transaction_id': getattr(payment, 'transaction_id', None)
        },
        content_object=payment
    )


def notify_payment_failed_pending(payment, status='failed'):
    """
    Notify relevant parties when payment fails or is pending
    """
    recipient = payment.freelancer if hasattr(payment, 'freelancer') else payment.recipient
    sender = payment.client if hasattr(payment, 'client') else payment.sender
    
    if status == 'failed':
        title = "Payment Failed"
        message = f"Payment of ${payment.amount} has failed. Please check your payment method and try again."
        priority = 'urgent'
    else:  # pending
        title = "Payment Pending"
        message = f"Your payment of ${payment.amount} is currently being processed. We'll notify you once it's complete."
        priority = 'medium'
    
    # Notify recipient
    create_and_send_notification(
        user=recipient,
        title=title,
        message=message,
        notification_type='payment',
        priority=priority,
        action_url=f"/dashboard/payments/{payment.id}",
        action_text="View Payment Details",
        data={
            'payment_id': payment.id,
            'amount': str(payment.amount),
            'status': status,
            'sender_id': sender.id if sender else None
        },
        content_object=payment
    )
    
    # Also notify sender if payment failed
    if status == 'failed' and sender:
        create_and_send_notification(
            user=sender,
            title="Payment Failed",
            message=f"Payment of ${payment.amount} to {recipient.get_full_name() or recipient.username} has failed. Please try again.",
            notification_type='payment',
            priority='urgent',
            action_url=f"/dashboard/payments/{payment.id}",
            action_text="Retry Payment",
            data={
                'payment_id': payment.id,
                'amount': str(payment.amount),
                'status': status,
                'recipient_id': recipient.id
            },
            content_object=payment
        )


def notify_new_review_received(review):
    """
    Notify user when they receive a new review
    """
    reviewed_user = review.reviewed_user
    reviewer = review.reviewer
    
    create_and_send_notification(
        user=reviewed_user,
        title="New Review Received",
        message=f"{reviewer.get_full_name() or reviewer.username} left you a {review.rating}-star review.",
        notification_type='review',
        priority='medium',
        action_url=f"/dashboard/profile/reviews",
        action_text="View Review",
        data={
            'review_id': review.id,
            'reviewer_id': reviewer.id,
            'rating': review.rating,
            'review_text': review.comment[:100] if hasattr(review, 'comment') and review.comment else None
        },
        content_object=review
    )


def notify_rating_updated(user, new_average_rating, old_average_rating=None):
    """
    Notify user when their overall rating is updated
    """
    change = "increased" if old_average_rating and new_average_rating > old_average_rating else "updated"
    
    create_and_send_notification(
        user=user,
        title="Profile Rating Updated",
        message=f"Your profile rating has been {change} to {new_average_rating:.1f} stars!",
        notification_type='review',
        priority='low',
        action_url=f"/dashboard/profile/reviews",
        action_text="View Reviews",
        data={
            'new_rating': new_average_rating,
            'old_rating': old_average_rating,
            'rating_change': change
        }
    )


def notify_review_response_posted(review_response):
    """
    Notify reviewer when the reviewed user responds to their review
    """
    review = review_response.review
    reviewer = review.reviewer
    reviewed_user = review.reviewed_user
    
    create_and_send_notification(
        user=reviewer,
        title="Review Response Posted",
        message=f"{reviewed_user.get_full_name() or reviewed_user.username} responded to your review.",
        notification_type='review',
        priority='low',
        action_url=f"/dashboard/profile/reviews",
        action_text="View Response",
        data={
            'review_id': review.id,
            'response_id': review_response.id,
            'reviewed_user_id': reviewed_user.id
        },
        content_object=review_response
    )
