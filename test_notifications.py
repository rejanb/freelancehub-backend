#!/usr/bin/env python
"""
Test script to demonstrate all notification triggers
Run this from Django shell: python manage.py shell < test_notifications.py
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from users.models import CustomUser
from jobs.models import Job
from proposals.models import Proposal
from contracts.models import Contract, ContractAttachment
from payments.models import Payment
from reviews.models import Review, Rating, ReviewResponse
from projects.models import Project
from notifications.models import Notification
from notifications.utils import *
from django.utils import timezone
from datetime import date, timedelta

def create_test_data():
    """Create test users and basic data"""
    
    # Create test users
    client, created = CustomUser.objects.get_or_create(
        username='test_client',
        defaults={
            'email': 'client@test.com',
            'first_name': 'John',
            'last_name': 'Client',
            'role': 'client'
        }
    )
    
    freelancer, created = CustomUser.objects.get_or_create(
        username='test_freelancer',
        defaults={
            'email': 'freelancer@test.com',
            'first_name': 'Jane',
            'last_name': 'Freelancer',
            'role': 'freelancer'
        }
    )
    
    return client, freelancer

def test_proposal_notifications():
    """Test proposal submission notifications"""
    print("\\n=== Testing Proposal Notifications ===")
    
    client, freelancer = create_test_data()
    
    # Create a job
    job, created = Job.objects.get_or_create(
        title='Test Job for Notifications',
        defaults={
            'description': 'A test job to trigger notifications',
            'budget': Decimal('1000.00'),
            'user': client,
            'deadline': date.today() + timedelta(days=30)
        }
    )
    
    # Create a proposal (should trigger notification)
    proposal = Proposal.objects.create(
        job=job,
        freelancer=freelancer,
        cover_letter='Test proposal for notification testing',
        bid_amount=Decimal('800.00')
    )
    
    print(f"✓ Created proposal {proposal.id} - should notify client {client.username}")
    
    return proposal

def test_contract_notifications():
    """Test contract-related notifications"""
    print("\\n=== Testing Contract Notifications ===")
    
    proposal = test_proposal_notifications()
    
    # Accept proposal and create contract (should trigger notification)
    contract = Contract.objects.create(
        proposal=proposal,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        total_payment=proposal.bid_amount,
        status='active'
    )
    
    print(f"✓ Created contract {contract.id} - should notify freelancer")
    
    # Change contract status (should trigger notification)
    contract.status = 'completed'
    contract.save()
    
    print(f"✓ Changed contract status to completed - should notify both parties")
    
    return contract

def test_payment_notifications():
    """Test payment-related notifications"""
    print("\\n=== Testing Payment Notifications ===")
    
    contract = test_contract_notifications()
    
    # Create pending payment
    payment = Payment.objects.create(
        contract=contract,
        user=contract.freelancer,
        amount=contract.total_payment,
        status='pending'
    )
    
    print(f"✓ Created pending payment {payment.id} - should notify recipient")
    
    # Process payment successfully
    payment.status = 'completed'
    payment.transaction_id = 'TEST_TXN_123'
    payment.save()
    
    print(f"✓ Payment completed - should notify freelancer")
    
    # Create failed payment
    failed_payment = Payment.objects.create(
        contract=contract,
        user=contract.freelancer,
        amount=Decimal('100.00'),
        status='failed'
    )
    
    print(f"✓ Created failed payment - should notify both parties")
    
    return payment

def test_review_notifications():
    """Test review and rating notifications"""
    print("\\n=== Testing Review Notifications ===")
    
    client, freelancer = create_test_data()
    
    # Create a project for ratings
    project, created = Project.objects.get_or_create(
        title='Test Project for Reviews',
        defaults={
            'description': 'Test project for review notifications',
            'client': client,
            'budget': Decimal('500.00')
        }
    )
    
    # Create a review (should trigger notification)
    review = Review.objects.create(
        rating=5,
        comment='Excellent work on this project!',
        reviewer=client,
        reviewee=freelancer,
        content_object=project
    )
    
    print(f"✓ Created review {review.id} - should notify freelancer")
    
    # Create review response (should trigger notification)
    response = ReviewResponse.objects.create(
        review=review,
        response_text='Thank you for the great feedback!'
    )
    
    print(f"✓ Created review response - should notify reviewer")
    
    # Create a rating (should trigger notification)
    rating = Rating.objects.create(
        project=project,
        freelancer=freelancer,
        client=client,
        rated_by=client,
        rated_user=freelancer,
        rating=4,
        review='Good communication and quality work'
    )
    
    print(f"✓ Created rating {rating.id} - should notify freelancer")
    
    return review

def test_deliverable_notifications():
    """Test deliverable submission notifications"""
    print("\\n=== Testing Deliverable Notifications ===")
    
    # This would require file upload, so we'll simulate it
    # In real usage, this would trigger when ContractAttachment with type='deliverable' is created
    print("✓ Deliverable notifications are triggered when ContractAttachment with type='deliverable' is saved")

def test_deadline_notifications():
    """Test deadline approaching notifications"""
    print("\\n=== Testing Deadline Notifications ===")
    
    client, freelancer = create_test_data()
    
    # Create contract with deadline in 2 days
    job, created = Job.objects.get_or_create(
        title='Urgent Job',
        defaults={
            'description': 'Job with approaching deadline',
            'budget': Decimal('500.00'),
            'user': client,
            'deadline': date.today() + timedelta(days=7)
        }
    )
    
    proposal = Proposal.objects.create(
        job=job,
        freelancer=freelancer,
        cover_letter='Quick proposal',
        bid_amount=Decimal('450.00')
    )
    
    contract = Contract.objects.create(
        proposal=proposal,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=2),  # 2 days from now
        total_payment=proposal.bid_amount,
        status='active'
    )
    
    # Manually trigger deadline notification
    notify_contract_deadline_approaching(contract, 2)
    
    print(f"✓ Triggered deadline notification for contract {contract.id}")

def show_notifications_summary():
    """Show summary of created notifications"""
    print("\\n=== Notifications Summary ===")
    
    total_notifications = Notification.objects.count()
    print(f"Total notifications created: {total_notifications}")
    
    # Group by type
    by_type = {}
    for notification in Notification.objects.all():
        ntype = notification.notification_type
        if ntype not in by_type:
            by_type[ntype] = 0
        by_type[ntype] += 1
    
    for ntype, count in by_type.items():
        print(f"  {ntype}: {count}")
    
    # Show recent notifications
    print("\\nRecent notifications:")
    for notification in Notification.objects.order_by('-created_at')[:10]:
        print(f"  [{notification.notification_type}] {notification.title} -> {notification.user.username}")

if __name__ == '__main__':
    print("Starting notification system tests...")
    
    # Clear existing test notifications
    Notification.objects.filter(
        user__username__in=['test_client', 'test_freelancer']
    ).delete()
    
    # Run all tests
    test_proposal_notifications()
    test_contract_notifications()
    test_payment_notifications()
    test_review_notifications()
    test_deliverable_notifications()
    test_deadline_notifications()
    
    # Show summary
    show_notifications_summary()
    
    print("\\n=== Notification Tests Complete ===")
    print("Check your notification dashboard to see the results!")
