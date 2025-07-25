#!/usr/bin/env python3
"""
Enhanced test script for debugging real-time notifications
"""

import os
import sys
import django
from pathlib import Path
import time

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from notifications.utils import notify_system_alert
from notifications.models import Notification
from datetime import datetime

User = get_user_model()

def debug_notification_system():
    """Debug the entire notification system"""
    print("🔍 DEBUGGING NOTIFICATION SYSTEM")
    print("=" * 50)
    
    # Check users
    users = User.objects.all()
    print(f"📊 Total users in database: {users.count()}")
    
    if not users:
        print("❌ No users found! Create a user first.")
        return
    
    user = users.first()
    print(f"👤 Testing with user: {user.username} (ID: {user.id})")
    
    # Check existing notifications
    existing_count = Notification.objects.filter(user=user).count()
    print(f"📬 Existing notifications for user: {existing_count}")
    
    # Send test notification
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"\n🚀 Sending test notification at {timestamp}")
    
    notify_system_alert(
        user=user,
        title=f"🔧 Debug Test {timestamp}",
        message=f"Real-time test notification sent at {timestamp}. This should appear instantly in your browser without refresh!",
        action_url="/notifications/",
        action_text="View Notifications"
    )
    
    # Verify notification was created
    new_count = Notification.objects.filter(user=user).count()
    print(f"✅ Notification created! Total count: {existing_count} → {new_count}")
    
    # Show the latest notification
    latest = Notification.objects.filter(user=user).order_by('-created_at').first()
    if latest:
        print(f"📝 Latest notification:")
        print(f"   Title: {latest.title}")
        print(f"   Message: {latest.message}")
        print(f"   Created: {latest.created_at}")
        print(f"   Read: {'Yes' if latest.read_at else 'No'}")
    
    print(f"\n🎯 WHAT TO CHECK IN YOUR BROWSER:")
    print(f"1. Open browser console (F12)")
    print(f"2. Look for: 'WebSocket message received: ...'")
    print(f"3. Check if notification appears without refresh")
    print(f"4. Verify notification count updates")
    print(f"5. 🍞 LOOK FOR TOAST NOTIFICATION in top-right corner!")
    
    print(f"\n💡 If real-time doesn't work, check:")
    print(f"   - WebSocket connection status in browser console")
    print(f"   - Are you logged into the frontend?")
    print(f"   - Are you on the notifications page?")
    print(f"   - Network tab for WebSocket messages")
    print(f"   - Toast notifications should appear automatically!")

if __name__ == "__main__":
    try:
        debug_notification_system()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
