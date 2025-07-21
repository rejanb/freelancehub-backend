import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from contracts.models import Contract
from jobs.models import Job
from proposals.models import Proposal

User = get_user_model()

@pytest.mark.django_db
def test_create_payment_intent():
   
    user = User.objects.create_user(username="payer", email="pay@me.com", password="1234")
    freelancer = User.objects.create_user(username="f", email="f@pay.com", password="1234")

  
    if hasattr(user, 'user_type'):
        user.user_type = "client"
        user.save()
    if hasattr(freelancer, 'user_type'):
        freelancer.user_type = "freelancer"
        freelancer.save()

 
    job = Job.objects.create(client=user, title="Draw", description="Need artist", budget=100, deadline="2099-01-01")
    proposal = Proposal.objects.create(job=job, freelancer=freelancer, cover_letter="Let’s do it", bid_amount=90)
    contract = Contract.objects.create(proposal=proposal, start_date="2024-01-01", status="active", total_payment=90)

    
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post("/api/payments/create-payment-intent/", {
        "amount": "90.00",
        "contract_id": contract.id
    }, format="json")

   
    assert response.status_code == 200
    assert "clientSecret" in response.json()
