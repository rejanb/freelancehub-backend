import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.mark.django_db
def test_project_creation():
    user = User.objects.create_user(username="client", email="c@p.com", password="1234")
    
   
    if hasattr(user, 'user_type'):
        user.user_type = "client"
        user.save()

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post("/api/projects/", {
        "title": "Mobile App",
        "description": "Cross-platform needed",
        "budget": 5000,
        "deadline": "2099-12-31",
        "status": "open"
    }, format="json")

    assert response.status_code == 201
