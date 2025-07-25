#!/usr/bin/env python3
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def update_user_names():
    """Update users with proper first and last names"""
    
    # Get user with username "haa" and set their name
    try:
        user1 = User.objects.get(username="haa")
        user1.first_name = "John"
        user1.last_name = "Doe"
        user1.save()
        print(f"Updated user {user1.username}: {user1.first_name} {user1.last_name}")
    except User.DoesNotExist:
        print("User 'haa' not found")
    
    # Get user with username "haas" and set their name
    try:
        user2 = User.objects.get(username="haas")
        user2.first_name = "Jane"
        user2.last_name = "Smith"
        user2.save()
        print(f"Updated user {user2.username}: {user2.first_name} {user2.last_name}")
    except User.DoesNotExist:
        print("User 'haas' not found")
    
    # Display all users with their names
    print("\nAll users:")
    for user in User.objects.all():
        print(f"ID: {user.id}, Username: {user.username}, Name: {user.first_name} {user.last_name}, Email: {user.email}")

if __name__ == "__main__":
    update_user_names()
