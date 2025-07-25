#!/usr/bin/env python3
"""
Real-time Chat Test - Simple WebSocket test for chat functionality
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

WS_URL = 'ws://localhost:8000'

async def test_chat_websocket():
    """Test WebSocket chat functionality"""
    print("🚀 Starting Real-time Chat Test")
    print("=" * 50)
    
    # Test with room ID 1 (adjust as needed)
    room_id = input("Enter chat room ID to test (default: 1): ").strip() or "1"
    
    try:
        ws_url = f'{WS_URL}/ws/chat/{room_id}/'
        print(f"📡 Connecting to: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully!")
            print("💬 You can now send messages. Type 'quit' to exit.")
            print("-" * 50)
            
            # Start listening for messages
            async def listen_for_messages():
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if data.get('type') == 'chat_message':
                            msg_data = data.get('message', {})
                            sender = msg_data.get('sender', {}).get('username', 'Unknown')
                            content = msg_data.get('content', '')
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"📨 [{timestamp}] {sender}: {content}")
                        else:
                            print(f"📢 System: {data}")
                            
                except websockets.exceptions.ConnectionClosed:
                    print("❌ Connection closed")
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
            
            # Start listening task
            listen_task = asyncio.create_task(listen_for_messages())
            
            # Send messages
            try:
                while True:
                    user_input = input()
                    
                    if user_input.lower() == 'quit':
                        break
                    
                    if user_input.strip():
                        message_data = {
                            'message': user_input,
                            'type': 'chat_message'
                        }
                        
                        await websocket.send(json.dumps(message_data))
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"📤 [{timestamp}] You: {user_input}")
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
            finally:
                listen_task.cancel()
                
    except websockets.exceptions.InvalidURI:
        print("❌ Invalid WebSocket URL")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Connection was closed")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure your Django server is running with WebSocket support")

if __name__ == "__main__":
    print("Real-time Chat WebSocket Test")
    print("Make sure your Django server is running on localhost:8000")
    print()
    
    try:
        asyncio.run(test_chat_websocket())
    except KeyboardInterrupt:
        print("\n👋 Test stopped by user")
