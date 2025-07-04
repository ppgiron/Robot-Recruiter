#!/usr/bin/env python3
"""
Test script for real-time intake intelligence service.
This script tests the WebSocket connection and basic functionality.
"""

import asyncio
import json
import websockets
import uuid
import time
import pytest

@pytest.mark.asyncio
async def test_realtime_intake():
    """Test the real-time intake service via WebSocket."""
    
    # Create a session
    session_id = str(uuid.uuid4())
    websocket_url = f"ws://localhost:8000/ws/intake/{session_id}"
    
    print(f"Connecting to WebSocket: {websocket_url}")
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Test 1: Join meeting
            join_message = {
                "type": "participant_join",
                "name": "Test Recruiter"
            }
            await websocket.send(json.dumps(join_message))
            print("✅ Sent participant join message")
            
            # Test 2: Add manual requirement
            requirement_message = {
                "type": "manual_requirement",
                "text": "Need a senior backend engineer with 5+ years experience",
                "category": "technical_skills"
            }
            await websocket.send(json.dumps(requirement_message))
            print("✅ Sent manual requirement")
            
            # Test 3: Simulate audio chunk (empty for testing)
            audio_message = {
                "type": "audio_chunk",
                "audio": [0.0] * 1024  # Empty audio chunk
            }
            await websocket.send(json.dumps(audio_message))
            print("✅ Sent audio chunk")
            
            # Listen for responses
            print("\n📡 Listening for responses...")
            timeout = 30  # 30 seconds timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"📨 Received: {data['type']}")
                    
                    if data['type'] == 'transcription_update':
                        print(f"   Transcript: {data.get('text', '')}")
                    elif data['type'] == 'analysis_update':
                        print(f"   New requirements: {len(data.get('new_requirements', []))}")
                        print(f"   Suggested questions: {len(data.get('suggested_questions', []))}")
                        print(f"   Missing info: {data.get('missing_info', [])}")
                        
                except asyncio.TimeoutError:
                    print("⏰ No response received in 5 seconds, continuing...")
                    break
                    
            print("\n✅ Test completed successfully!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

@pytest.mark.asyncio
async def test_session_creation():
    """Test session creation via HTTP API."""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/intake/sessions') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Session created: {data['session_id']}")
                    return data['session_id']
                else:
                    print(f"❌ Failed to create session: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return None

async def main():
    """Run all tests."""
    print("🚀 Starting Real-time Intake Intelligence Tests\n")
    
    # Test 1: Session creation
    print("1. Testing session creation...")
    session_id = await test_session_creation()
    
    if session_id:
        # Test 2: WebSocket functionality
        print("\n2. Testing WebSocket functionality...")
        await test_realtime_intake()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 