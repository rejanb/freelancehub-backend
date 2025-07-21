import pytest
from users.models import CustomUser as User
from disputes.models import Dispute
from contracts.models import Contract
from jobs.models import Job
from proposals.models import Proposal
from django.contrib.contenttypes.models import ContentType

@pytest.mark.django_db
def test_dispute_creation():
    client = User.objects.create_user(username="client", email="client@dispute.com", password="pass", user_type="client")
    freelancer = User.objects.create_user(username="freelancer", email="free@dispute.com", password="pass", user_type="freelancer")
    
    job = Job.objects.create(client=client, title="Site", description="Build it", budget=100, deadline="2099-01-01")
    proposal = Proposal.objects.create(job=job, freelancer=freelancer, cover_letter="Yes", bid_amount=90)
    contract = Contract.objects.create(proposal=proposal, start_date="2024-01-01", status="active", total_payment=90)
    
    content_type = ContentType.objects.get_for_model(Contract)
    dispute = Dispute.objects.create(
        reason="Unfinished work",
        description="Freelancer stopped responding",
        created_by=client,
        content_type=content_type,
        object_id=contract.id
    )

    assert dispute.status == "open"
    assert dispute.reason == "Unfinished work"
