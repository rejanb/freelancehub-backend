#!/usr/bin/env python3

import os
import sys
import django
import requests
import json
from django.contrib.auth import get_user_model

# Add the project directory to Python path
sys.path.append('/Users/rejan/Documents/Epita/Action Learning /final')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

def test_chat_endpoint():
    """Test the chat endpoint that's failing"""
    
    # First, let's check if we have users in the database
    User = get_user_model()
    users = User.objects.all()[:5]  # Get first 5 users
    
    print("Available users:")
    for user in users:
        print(f"  ID: {user.id}, Username: {user.username}, Email: {user.email}")
    
    if len(users) < 2:
        print("\nError: Need at least 2 users to test chat functionality")
        return
    
    # Test data
    user1 = users[0]
    user2 = users[1]
    
    print(f"\nTesting chat creation between User {user1.id} ({user1.username}) and User {user2.id} ({user2.username})")
    
    # Make the API request
    url = "http://localhost:8000/api/chats/api/chatrooms/get_or_create_with_user/"
    
    # We need to authenticate - let's try to get a token or session
    # For now, let's test the view directly
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    from chats.views import ChatRoomViewSet
    
    factory = RequestFactory()
    request = factory.post(url, {
        'user_id': user2.id
    }, content_type='application/json')
    
    # Authenticate the request
    request.user = user1
    
    # Test the view
    viewset = ChatRoomViewSet()
    viewset.action = 'get_or_create_with_user'
    viewset.request = request
    
    try:
        response = viewset.get_or_create_with_user(request)
        print(f"Success! Status: {response.status_code}")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_endpoint()
