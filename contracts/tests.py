import pytest
from users.models import CustomUser as User
from jobs.models import Job
from proposals.models import Proposal
from contracts.models import Contract

@pytest.mark.django_db
def test_contract_creation():
    client_user = User.objects.create_user(username="c", email="c@con.com", password="1234")
    freelancer = User.objects.create_user(username="f", email="f@con.com", password="1234")

    client_user.user_type = "client"
    client_user.save()
    freelancer.user_type = "freelancer"
    freelancer.save()

    job = Job.objects.create(
        client=client_user,
        title="Write Docs",
        description="API docs",
        budget=300,
        deadline="2099-01-01"
    )
    proposal = Proposal.objects.create(
        job=job,
        freelancer=freelancer,
        cover_letter="Sure",
        bid_amount=250
    )
    contract = Contract.objects.create(
        proposal=proposal,
        start_date="2024-01-01",
        status="active",
        total_payment=250
    )
    assert contract.status == "active"
