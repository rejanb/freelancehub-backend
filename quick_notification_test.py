#!/usr/bin/env python3
"""
Quick notification sender that can run while the main server is running.
This sends notifications directly through Django ORM without using HTTP APIs.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from notifications.utils import notify_system_alert, notify_new_proposal_submitted
from datetime import datetime

User = get_user_model()

def send_test_notification():
    """Send a test notification while server is running"""
    print("🔍 Looking for users...")
    
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        print("💡 Create a user first through the frontend or Django admin")
        return
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"📤 Sending real-time test notification to: {user.username} (ID: {user.id}) at {timestamp}")
    
    # Send test notification
    notify_system_alert(
        user=user,
        title="⚡ Real-time Test",
        message=f"WebSocket test notification sent at {timestamp}. If you see this instantly without refreshing the page, real-time notifications are working perfectly! 🎉",
        action_url="/notifications/",
        action_text="View All Notifications"
    )
    
    print("✅ Notification sent successfully!")
    print("👀 Check your frontend - it should appear instantly!")
    print("🔧 If it doesn't appear, check:")
    print("   - Browser console for WebSocket connection logs")
    print("   - Network tab for WebSocket messages")
    print("   - Make sure you're logged in to the frontend")

def send_proposal_notification():
    """Send a proposal notification for more realistic testing"""
    user = User.objects.first()
    if not user:
        print("❌ No users found")
        return
        
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"📤 Sending proposal notification to: {user.username} at {timestamp}")
    
    notify_new_proposal_submitted(
        user=user,
        proposal_title="Test Web Development Project",
        job_title="Build a Real-time Dashboard",
        action_url="/proposals/123/"
    )
    
    print("✅ Proposal notification sent!")

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "proposal":
            send_proposal_notification()
        else:
            send_test_notification()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure Django server is running and database is accessible")
