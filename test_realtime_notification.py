#!/usr/bin/env python
"""
Test script to send a real-time notification
"""
import os
import django
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from notifications.utils import notify_system_alert
from users.models import User

def send_test_notification():
    """Send a test notification to the first user"""
    try:
        # Get the first user (you can change this to a specific user ID)
        user = User.objects.first()
        if not user:
            print("No users found in the database")
            return
        
        print(f"Sending test notification to user: {user.username} (ID: {user.id})")
        
        # Send a test system notification
        notify_system_alert(
            user=user,
            title="🧪 Test Notification",
            message="This is a real-time test notification to verify WebSocket functionality is working correctly!",
            action_url="/notifications/",
            action_text="View Notifications"
        )
        
        print("✅ Test notification sent successfully!")
        print("Check your frontend to see if it appears in real-time without refreshing.")
        
    except Exception as e:
        print(f"❌ Error sending test notification: {e}")

if __name__ == "__main__":
    send_test_notification()
