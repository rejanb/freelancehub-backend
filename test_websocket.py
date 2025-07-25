import asyncio
import websockets
import json

async def test_websocket():
    # Test token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUzMzQ0NDU1LCJpYXQiOjE3NTMzNDI2NTUsImp0aSI6IjU1ZTE2Nzg3MTVjMTQ2YzQ4Y2FmZjA3MWMyNTYyNGZiIiwidXNlcl9pZCI6OX0.DjMA5OekLmO054P4FMbnYZdyf547K_8vx9wGdwVnvNQ"
    
    uri = f"ws://localhost:8000/ws/notifications/?token={token}"
    
    try:
        print(f"Attempting to connect to: {uri}")
        async with websockets.connect(uri) as websocket:
            print("WebSocket connection established!")
            
            # Send a ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
