from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Project, Category

User = get_user_model()

class ProjectAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testclient", 
            email="test@example.com", 
            password="testpass123"
        )
        if hasattr(self.user, 'user_type'):
            self.user.user_type = "client"
            self.user.save()
        
        self.category = Category.objects.create(
            name="Test Category",
            description="Test category description"
        )
        
        self.client = APIClient()

    def test_project_creation(self):
        """Test creating a new project"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            "title": "Mobile App",
            "description": "Cross-platform mobile app needed",
            "budget": 5000,
            "deadline": "2099-12-31T00:00:00Z",
            "status": "open",
            "category_id": self.category.id
        }
        
        response = self.client.post("/api/projects/projects/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Mobile App")
        self.assertEqual(response.data["client"]["id"], self.user.id)

    def test_get_projects_public(self):
        """Test getting projects without authentication"""
        # Create a public project
        project = Project.objects.create(
            title="Public Project",
            description="A public project",
            budget=1000,
            deadline="2099-12-31",
            client=self.user,
            is_public=True
        )
        
        response = self.client.get("/api/projects/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_get_categories(self):
        """Test getting categories list"""
        response = self.client.get("/api/projects/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertTrue(len(response.data["results"]) > 0)

    def test_project_creation_requires_auth(self):
        """Test that creating a project requires authentication"""
        data = {
            "title": "Mobile App",
            "description": "Cross-platform mobile app needed",
            "budget": 5000,
            "deadline": "2099-12-31T00:00:00Z",
            "status": "open"
        }
        
        response = self.client.post("/api/projects/projects/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
