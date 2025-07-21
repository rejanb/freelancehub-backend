
from users.models import CustomUser as User
from rest_framework.test import APIClient
from jobs.models import Job
import pytest

@pytest.mark.django_db
def test_submit_proposal():
    client_user = User.objects.create_user(username="client", email="c@j.com", password="pass", user_type="client")
    freelancer = User.objects.create_user(username="freelancer", email="f@j.com", password="pass", user_type="freelancer")

    job = Job.objects.create(
        client=client_user,
        title="Design Logo",
        description="Creative designer",
        budget=200,
        deadline="2099-12-31"
    )

    client = APIClient()
    client.force_authenticate(user=freelancer)

    response = client.post("/api/proposals/", {
        "job": job.id,
        "cover_letter": "I can do this job",
        "bid_amount": 150
    }, format="json")

    assert response.status_code == 201
