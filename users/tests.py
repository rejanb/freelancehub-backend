import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import CustomUser

@pytest.mark.django_db
def test_user_registration():
    client = APIClient()
    response = client.post(reverse("register"), {
        "username": "johndoe",
        "email": "john@example.com",
        "password": "password123",
        "password_confirm": "password123",
        "user_type": "freelancer",
        "bio": "Experienced developer",
        "skills": ["python"]
    }, format="json")
    assert response.status_code == 201
    assert CustomUser.objects.filter(email="john@example.com").exists()

