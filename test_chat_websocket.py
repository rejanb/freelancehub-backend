import asyncio
import websockets
import json

async def test_chat_websocket():
    # Test token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUzMzQ3NDU4LCJpYXQiOjE3NTMzNDU2NTgsImp0aSI6IjczMTkyYzA2OTNkZjRlYWZiZTVmNGE2MWE3NjhlN2M1IiwidXNlcl9pZCI6OX0.Q8pP7V2xrff0Nmu1YbB7SAZ77RKEeiG00CmFGe1sObc"
    
    # Test chat room WebSocket (room 1)
    chat_uri = f"ws://localhost:8000/ws/chat/1/?token={token}"
    
    try:
        print(f"Attempting to connect to chat WebSocket: {chat_uri}")
        async with websockets.connect(chat_uri) as websocket:
            print("Chat WebSocket connection established!")
            
            # Send a test message
            test_message = {
                "type": "chat_message",
                "message": "Test message from WebSocket client"
            }
            await websocket.send(json.dumps(test_message))
            print("Test message sent")
            
            # Wait for any responses
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No response received within 5 seconds")
            
    except Exception as e:
        print(f"Chat WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat_websocket())
