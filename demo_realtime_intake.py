#!/usr/bin/env python3
"""
Comprehensive demo of the Real-time Intake Intelligence System.
This script simulates a complete intake meeting with live transcription,
requirement extraction, and intelligent question generation.
"""

import asyncio
import json
import websockets
import uuid
import time
import random
from datetime import datetime

class IntakeMeetingDemo:
    def __init__(self):
        self.session_id = None
        self.websocket = None
        self.meeting_scenario = [
            "Hi, I'm Sarah from TechCorp. We're looking to hire a senior backend engineer.",
            "The role requires experience with Python, Django, and PostgreSQL.",
            "We need someone who can work with distributed systems and microservices.",
            "The team is about 8 people, and we're looking to hire within the next 2 months.",
            "The salary range is $120k to $150k, and we offer remote work options.",
            "We're looking for someone with at least 5 years of experience.",
            "The person should be comfortable with AWS and Docker.",
            "We value good communication skills and experience mentoring junior developers."
        ]
        
    async def start_demo(self):
        """Run the complete demo."""
        print("🎯 REAL-TIME INTAKE INTELLIGENCE DEMO")
        print("=" * 50)
        
        # Step 1: Create session
        await self.create_session()
        
        # Step 2: Connect WebSocket
        await self.connect_websocket()
        
        # Step 3: Simulate meeting
        await self.simulate_meeting()
        
        # Step 4: Show results
        await self.show_results()
        
    async def create_session(self):
        """Create a new intake session."""
        print("\n1️⃣ Creating intake session...")
        
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('http://localhost:8000/intake/sessions') as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session_id = data['session_id']
                        print(f"✅ Session created: {self.session_id}")
                    else:
                        raise Exception(f"Failed to create session: {response.status}")
        except Exception as e:
            print(f"❌ Session creation failed: {e}")
            raise
    
    async def connect_websocket(self):
        """Connect to WebSocket."""
        print("\n2️⃣ Connecting to WebSocket...")
        
        websocket_url = f"ws://localhost:8000/ws/intake/{self.session_id}"
        
        try:
            self.websocket = await websockets.connect(websocket_url)
            print("✅ WebSocket connected successfully!")
            
            # Start listening for messages
            asyncio.create_task(self.listen_for_messages())
            
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            raise
    
    async def listen_for_messages(self):
        """Listen for incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("📡 WebSocket connection closed")
        except Exception as e:
            print(f"❌ Error in message listener: {e}")
    
    async def handle_message(self, data):
        """Handle incoming WebSocket messages."""
        message_type = data.get('type')
        
        if message_type == 'transcription_update':
            print(f"🎤 TRANSCRIPT: {data.get('text', '')}")
            
        elif message_type == 'analysis_update':
            new_reqs = data.get('new_requirements', [])
            new_questions = data.get('suggested_questions', [])
            missing_info = data.get('missing_info', [])
            
            if new_reqs:
                print(f"\n📋 NEW REQUIREMENTS:")
                for req in new_reqs:
                    print(f"   • {req['text']} ({req['category']}) - {req['confidence']:.0%}")
            
            if new_questions:
                print(f"\n❓ SUGGESTED QUESTIONS:")
                for q in new_questions:
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[q['priority']]
                    print(f"   {priority_emoji} {q['text']}")
                    print(f"      Reasoning: {q['reasoning']}")
            
            if missing_info:
                print(f"\n⚠️  MISSING INFORMATION:")
                for info in missing_info:
                    print(f"   • {info}")
    
    async def simulate_meeting(self):
        """Simulate a realistic intake meeting."""
        print("\n3️⃣ Simulating intake meeting...")
        
        # Join meeting
        await self.websocket.send(json.dumps({
            "type": "participant_join",
            "name": "Sarah (Hiring Manager)"
        }))
        print("👋 Sarah joined the meeting")
        
        # Simulate conversation
        for i, statement in enumerate(self.meeting_scenario):
            print(f"\n🗣️  Sarah: {statement}")
            
            # Send as manual requirement for demo purposes
            await self.websocket.send(json.dumps({
                "type": "manual_requirement",
                "text": statement,
                "category": self.categorize_statement(statement)
            }))
            
            # Wait for processing
            await asyncio.sleep(3)
            
            # Simulate some audio processing
            await self.simulate_audio_processing()
            
            # Wait between statements
            if i < len(self.meeting_scenario) - 1:
                await asyncio.sleep(2)
    
    def categorize_statement(self, statement):
        """Categorize a statement for demo purposes."""
        statement_lower = statement.lower()
        
        if any(word in statement_lower for word in ['python', 'django', 'postgresql', 'aws', 'docker']):
            return 'technical_skills'
        elif any(word in statement_lower for word in ['experience', 'years', 'senior']):
            return 'experience_level'
        elif any(word in statement_lower for word in ['team', 'people', 'mentoring']):
            return 'team_size'
        elif any(word in statement_lower for word in ['salary', '120k', '150k']):
            return 'salary'
        elif any(word in statement_lower for word in ['remote', 'work']):
            return 'location'
        elif any(word in statement_lower for word in ['months', 'timeline']):
            return 'timeline'
        else:
            return 'culture_fit'
    
    async def simulate_audio_processing(self):
        """Simulate audio processing for demo."""
        # Send empty audio chunk to trigger processing
        await self.websocket.send(json.dumps({
            "type": "audio_chunk",
            "audio": [0.0] * 1024
        }))
    
    async def show_results(self):
        """Show final meeting results."""
        print("\n4️⃣ Meeting Summary")
        print("=" * 30)
        
        # Get session summary
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:8000/intake/sessions/{self.session_id}/summary') as response:
                    if response.status == 200:
                        summary = await response.json()
                        print(f"📊 Session Duration: {summary.get('duration_minutes', 0):.1f} minutes")
                        print(f"📝 Transcript Length: {summary.get('transcript_length', 0)} characters")
                        print(f"📋 Requirements Extracted: {summary.get('requirements_count', 0)}")
                        print(f"❓ Questions Generated: {summary.get('questions_generated', 0)}")
                        print(f"⚠️  Missing Info Items: {len(summary.get('missing_info', []))}")
                        
                        if summary.get('missing_info'):
                            print("\nMissing Information:")
                            for info in summary['missing_info']:
                                print(f"   • {info}")
                    else:
                        print("❌ Could not retrieve session summary")
        except Exception as e:
            print(f"❌ Error getting summary: {e}")
        
        print("\n🎉 Demo completed!")
        print("\n💡 Key Features Demonstrated:")
        print("   • Real-time WebSocket communication")
        print("   • Live requirement extraction")
        print("   • Intelligent question generation")
        print("   • Missing information identification")
        print("   • Meeting state management")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.websocket:
            await self.websocket.close()

async def main():
    """Run the demo."""
    demo = IntakeMeetingDemo()
    
    try:
        await demo.start_demo()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    finally:
        await demo.cleanup()

if __name__ == "__main__":
    print("🚀 Starting Real-time Intake Intelligence Demo")
    print("Make sure the backend server is running on localhost:8000")
    print("Press Ctrl+C to stop the demo\n")
    
    asyncio.run(main()) 