#!/usr/bin/env python3
"""
Demo script to test all implemented notification types
Run this to see all notifications in action
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "test_user@example.com"
PASSWORD = "testpass123"

def get_auth_token():
    """Get JWT token for API requests"""
    response = requests.post(f"{BASE_URL}/users/login/", {
        "email": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get("access")
    else:
        print("❌ Failed to get auth token. Make sure user exists.")
        return None

def test_all_notifications(token):
    """Test all notification types"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔔 Testing all notification types...")
    
    response = requests.post(f"{BASE_URL}/notifications/test-all/", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Notifications sent successfully!")
        for item in result.get("results", []):
            print(f"   {item}")
    else:
        print(f"❌ Failed to send notifications: {response.text}")

def get_notifications(token):
    """Fetch and display notifications"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/notifications/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        notifications = data.get("results", [])
        
        print(f"\\n📬 Found {len(notifications)} notifications:")
        print("-" * 60)
        
        for notification in notifications[:10]:  # Show latest 10
            status = "🔴 UNREAD" if not notification.get("read_at") else "✅ READ"
            type_icon = {
                'proposal': '📋',
                'contract': '📄', 
                'payment': '💰',
                'review': '⭐',
                'job': '💼',
                'system': '⚙️'
            }.get(notification.get("notification_type"), '📢')
            
            print(f"{type_icon} [{notification.get('notification_type').upper()}] {status}")
            print(f"   Title: {notification.get('title')}")
            print(f"   Message: {notification.get('message')[:80]}...")
            print(f"   Priority: {notification.get('priority')}")
            print(f"   Created: {notification.get('created_at')}")
            if notification.get('action_text'):
                print(f"   Action: {notification.get('action_text')}")
            print()
    else:
        print(f"❌ Failed to get notifications: {response.text}")

def create_test_user():
    """Create a test user if it doesn't exist"""
    user_data = {
        "username": "testuser",
        "email": USERNAME,
        "password": PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "role": "freelancer"
    }
    
    response = requests.post(f"{BASE_URL}/users/register/", user_data)
    
    if response.status_code in [200, 201]:
        print("✅ Test user created or already exists")
        return True
    else:
        print(f"ℹ️  User creation response: {response.status_code}")
        return True  # User might already exist

def main():
    """Main demo function"""
    print("🚀 FreelanceHub Notification System Demo")
    print("=" * 50)
    
    # Create test user
    create_test_user()
    time.sleep(1)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        return
    
    print(f"✅ Authenticated successfully")
    time.sleep(1)
    
    # Test all notification types
    test_all_notifications(token)
    time.sleep(2)
    
    # Display notifications
    get_notifications(token)
    
    print("\\n🎉 Demo completed!")
    print("\\nNotification Types Demonstrated:")
    print("• 📋 New proposal submitted")
    print("• 📄 Proposal accepted → Contract created")
    print("• 📄 Contract status changes")
    print("• ⏰ Contract deadline approaching")
    print("• 📁 Deliverables submitted")
    print("• 💰 Payment processed successfully")
    print("• 💰 Payment failed/pending")
    print("• ⭐ New review received")
    print("• ⭐ Rating updated")
    print("• ⭐ Review response posted")
    
    print("\\n🌐 Check the frontend at http://localhost:4200/dashboard/notifications")

if __name__ == "__main__":
    main()
