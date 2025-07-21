import pytest
from users.models import CustomUser as User  
from jobs.models import Job

@pytest.mark.django_db
def test_create_job():
    user = User.objects.create_user(
        username="client",
        email="c@example.com",
        password="1234",
        user_type="client"
    )

    job = Job.objects.create(
        client=user,
        title="Test Job",
        description="This is a test",
        budget=1000,
        deadline="2099-01-01"
    )

    assert job.pk is not None
    assert job.client == user
