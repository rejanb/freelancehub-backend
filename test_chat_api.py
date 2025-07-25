#!/usr/bin/env python3
"""
Comprehensive Chat System Test
Tests all chat functionality including API endpoints, WebSocket connections, and real-time messaging
"""

import requests
import json
import time
import asyncio
import websockets
import sys
import os
from datetime import datetime

# Add Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelancehub_backend.settings')

# Base URLs
BASE_URL = 'http://localhost:8000'
WS_URL = 'ws://localhost:8000'

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

class ChatTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.username = None
        self.test_user_id = None
        self.chat_room_id = None
        
    def authenticate(self):
        """Login and get authentication token"""
        print_info("Authenticating user...")
        
        # Login credentials (adjust as needed)
        login_data = {
            'username': 'test@example.com',  # Change to your test user
            'password': 'testpass123'
        }
        
        try:
            response = self.session.post(f'{BASE_URL}/api/auth/login/', json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.user_id = data.get('user', {}).get('id')
                self.username = data.get('user', {}).get('username')
                
                # Set authorization header
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print_success(f"Authenticated as {self.username} (ID: {self.user_id})")
                return True
            else:
                print_error(f"Authentication failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Authentication error: {str(e)}")
            return False
    
    def get_or_create_test_user(self):
        """Create a test user for chat testing"""
        print_info("Getting or creating test user...")
        
        # Try to get existing users first
        try:
            response = self.session.get(f'{BASE_URL}/api/users/')
            if response.status_code == 200:
                users = response.json().get('results', [])
                # Find a user that's not the current user
                for user in users:
                    if user['id'] != self.user_id:
                        self.test_user_id = user['id']
                        print_success(f"Found test user: {user.get('username')} (ID: {self.test_user_id})")
                        return True
                        
                print_warning("No other users found, current user will chat with themselves")
                self.test_user_id = self.user_id
                return True
        except Exception as e:
            print_error(f"Error getting users: {str(e)}")
            self.test_user_id = self.user_id
            return True
    
    def test_chat_room_creation(self):
        """Test creating or getting a chat room"""
        print_info("Testing chat room creation...")
        
        try:
            # Create/get chat room with test user
            data = {'user_id': self.test_user_id}
            response = self.session.post(f'{BASE_URL}/api/chats/api/chatrooms/get_or_create_with_user/', json=data)
            
            if response.status_code in [200, 201]:
                chat_room = response.json()
                self.chat_room_id = chat_room.get('id')
                participants = chat_room.get('participants', [])
                participant_names = [p.get('username', 'Unknown') for p in participants]
                
                print_success(f"Chat room created/retrieved (ID: {self.chat_room_id})")
                print_info(f"Participants: {', '.join(participant_names)}")
                return True
            else:
                print_error(f"Failed to create chat room: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Chat room creation error: {str(e)}")
            return False
    
    def test_get_chat_rooms(self):
        """Test retrieving user's chat rooms"""
        print_info("Testing chat rooms retrieval...")
        
        try:
            response = self.session.get(f'{BASE_URL}/api/chats/api/chatrooms/')
            
            if response.status_code == 200:
                data = response.json()
                rooms = data.get('results', []) if 'results' in data else data
                print_success(f"Retrieved {len(rooms)} chat rooms")
                
                for i, room in enumerate(rooms[:3]):  # Show first 3 rooms
                    participants = room.get('participants', [])
                    participant_names = [p.get('username', 'Unknown') for p in participants]
                    last_message = room.get('last_message')
                    last_msg_preview = last_message.get('content', 'No messages')[:50] if last_message else 'No messages'
                    
                    print_info(f"  Room {i+1}: {', '.join(participant_names)} - '{last_msg_preview}...'")
                
                return True
            else:
                print_error(f"Failed to get chat rooms: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Get chat rooms error: {str(e)}")
            return False
    
    def test_send_message(self):
        """Test sending a message via API"""
        print_info("Testing message sending...")
        
        if not self.chat_room_id:
            print_error("No chat room available for testing")
            return False
        
        try:
            message_data = {
                'chat_room': self.chat_room_id,
                'content': f'Test message from API at {datetime.now().strftime("%H:%M:%S")}',
                'message_type': 'text'
            }
            
            response = self.session.post(f'{BASE_URL}/api/chats/api/messages/', json=message_data)
            
            if response.status_code == 201:
                message = response.json()
                print_success(f"Message sent successfully (ID: {message.get('id')})")
                print_info(f"Content: '{message.get('content')}'")
                return True
            else:
                print_error(f"Failed to send message: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Send message error: {str(e)}")
            return False
    
    def test_get_messages(self):
        """Test retrieving messages from a chat room"""
        print_info("Testing messages retrieval...")
        
        if not self.chat_room_id:
            print_error("No chat room available for testing")
            return False
        
        try:
            params = {'chat_room': self.chat_room_id}
            response = self.session.get(f'{BASE_URL}/api/chats/api/messages/', params=params)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('results', []) if 'results' in data else data
                print_success(f"Retrieved {len(messages)} messages")
                
                # Show last 3 messages
                for i, msg in enumerate(messages[-3:]):
                    sender = msg.get('sender', {}).get('username', 'Unknown')
                    content = msg.get('content', '')[:50]
                    timestamp = msg.get('created_at', '')
                    print_info(f"  {sender}: '{content}...' ({timestamp})")
                
                return True
            else:
                print_error(f"Failed to get messages: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Get messages error: {str(e)}")
            return False
    
    def test_mark_messages_read(self):
        """Test marking messages as read"""
        print_info("Testing mark messages as read...")
        
        if not self.chat_room_id:
            print_error("No chat room available for testing")
            return False
        
        try:
            response = self.session.post(f'{BASE_URL}/api/chats/api/chatrooms/{self.chat_room_id}/mark_read/')
            
            if response.status_code == 200:
                result = response.json()
                print_success(f"Messages marked as read: {result.get('message', 'Success')}")
                return True
            else:
                print_error(f"Failed to mark messages as read: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Mark messages read error: {str(e)}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket real-time chat functionality"""
        print_info("Testing WebSocket connection...")
        
        if not self.chat_room_id:
            print_error("No chat room available for WebSocket testing")
            return False
        
        try:
            # WebSocket URL for the chat room
            ws_url = f'{WS_URL}/ws/chat/{self.chat_room_id}/'
            
            # Add authorization header for WebSocket
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            print_info(f"Connecting to WebSocket: {ws_url}")
            
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                print_success("WebSocket connected successfully!")
                
                # Send a test message via WebSocket
                test_message = {
                    'message': f'WebSocket test message at {datetime.now().strftime("%H:%M:%S")}',
                    'type': 'chat_message'
                }
                
                await websocket.send(json.dumps(test_message))
                print_success("Test message sent via WebSocket")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message_data = json.loads(response)
                    print_success("Received WebSocket response:")
                    print_info(f"  Type: {message_data.get('type')}")
                    print_info(f"  Message: {message_data.get('message', {}).get('content', 'N/A')}")
                    
                except asyncio.TimeoutError:
                    print_warning("No WebSocket response received within 5 seconds")
                
                return True
                
        except websockets.exceptions.ConnectionClosed as e:
            print_error(f"WebSocket connection closed: {e}")
            return False
        except Exception as e:
            print_error(f"WebSocket error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all chat functionality tests"""
        print_header("FREELANCEHUB CHAT SYSTEM TEST")
        
        test_results = []
        
        # Authentication test
        if self.authenticate():
            test_results.append(("Authentication", True))
        else:
            test_results.append(("Authentication", False))
            print_error("Cannot proceed without authentication")
            return
        
        # Get test user
        if self.get_or_create_test_user():
            test_results.append(("Test User Setup", True))
        else:
            test_results.append(("Test User Setup", False))
        
        # Chat room creation test
        if self.test_chat_room_creation():
            test_results.append(("Chat Room Creation", True))
        else:
            test_results.append(("Chat Room Creation", False))
        
        # Get chat rooms test
        if self.test_get_chat_rooms():
            test_results.append(("Get Chat Rooms", True))
        else:
            test_results.append(("Get Chat Rooms", False))
        
        # Send message test
        if self.test_send_message():
            test_results.append(("Send Message", True))
        else:
            test_results.append(("Send Message", False))
        
        # Get messages test
        if self.test_get_messages():
            test_results.append(("Get Messages", True))
        else:
            test_results.append(("Get Messages", False))
        
        # Mark messages read test
        if self.test_mark_messages_read():
            test_results.append(("Mark Messages Read", True))
        else:
            test_results.append(("Mark Messages Read", False))
        
        # WebSocket test
        if await self.test_websocket_connection():
            test_results.append(("WebSocket Real-time", True))
        else:
            test_results.append(("WebSocket Real-time", False))
        
        # Print results summary
        print_header("TEST RESULTS SUMMARY")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            if result:
                print_success(f"{test_name}")
                passed += 1
            else:
                print_error(f"{test_name}")
        
        print(f"\n{Colors.BOLD}Total Tests: {total}{Colors.ENDC}")
        print(f"{Colors.OKGREEN if passed == total else Colors.WARNING}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL if passed < total else Colors.OKGREEN}Failed: {total - passed}{Colors.ENDC}")
        
        if passed == total:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL CHAT FUNCTIONALITY TESTS PASSED! 🎉{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  Some tests failed. Check the issues above.{Colors.ENDC}")

async def main():
    """Main function to run the chat tests"""
    tester = ChatTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("Starting FreelanceHub Chat System Test...")
    print("Make sure your Django server is running on localhost:8000")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {str(e)}{Colors.ENDC}")
