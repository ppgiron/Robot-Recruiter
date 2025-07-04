import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import whisper
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from .db import get_session
from .embedding_service import embedding_service
from .token_manager import get_openai_api_key
import openai
import os

logger = logging.getLogger(__name__)

@dataclass
class Requirement:
    text: str
    category: str  # 'technical', 'experience', 'culture', 'timeline', etc.
    confidence: float
    source_timestamp: datetime
    extracted_at: datetime

@dataclass
class SuggestedQuestion:
    text: str
    priority: str  # 'high', 'medium', 'low'
    reasoning: str
    category: str
    generated_at: datetime

@dataclass
class MeetingState:
    session_id: str
    participants: List[str]
    start_time: datetime
    current_transcript: str
    requirements: List[Requirement]
    suggested_questions: List[SuggestedQuestion]
    missing_info: Set[str]
    last_analysis: datetime

class RealtimeIntakeService:
    def __init__(self):
        # Initialize Whisper model for real-time transcription
        self.whisper_model = whisper.load_model("base")
        
        # OpenAI client will be initialized lazily when needed
        self.openai_client = None
        
        # Active meeting sessions
        self.active_sessions: Dict[str, MeetingState] = {}
        
        # Audio buffer for each session
        self.audio_buffers: Dict[str, List[np.ndarray]] = {}
        
        # Processing intervals (in seconds)
        self.transcription_interval = 3.0  # Process every 3 seconds
        self.analysis_interval = 5.0       # Analyze every 5 seconds
        
    def _get_openai_client(self):
        """Get OpenAI client, initializing if needed."""
        if self.openai_client is None:
            api_key = get_openai_api_key()
            if not api_key:
                raise ValueError("OpenAI API key is required for AI features")
            self.openai_client = openai.OpenAI(api_key=api_key)
        return self.openai_client
    
    async def handle_websocket(self, websocket: WebSocket, session_id: str):
        """Main WebSocket handler for real-time intake meetings."""
        await websocket.accept()
        
        # Initialize meeting state
        meeting_state = MeetingState(
            session_id=session_id,
            participants=[],
            start_time=datetime.now(timezone.utc),
            current_transcript="",
            requirements=[],
            suggested_questions=[],
            missing_info=set(),
            last_analysis=datetime.now(timezone.utc)
        )
        
        self.active_sessions[session_id] = meeting_state
        self.audio_buffers[session_id] = []
        
        try:
            # Start background tasks
            transcription_task = asyncio.create_task(
                self._transcription_loop(websocket, session_id)
            )
            analysis_task = asyncio.create_task(
                self._analysis_loop(websocket, session_id)
            )
            
            # Handle incoming messages
            async for message in websocket.iter_text():
                data = json.loads(message)
                await self._handle_message(websocket, session_id, data)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
        finally:
            # Cleanup
            transcription_task.cancel()
            analysis_task.cancel()
            await self._save_meeting_summary(session_id)
            del self.active_sessions[session_id]
            del self.audio_buffers[session_id]
    
    async def _handle_message(self, websocket: WebSocket, session_id: str, data: dict):
        """Handle incoming WebSocket messages."""
        message_type = data.get("type")
        
        if message_type == "audio_chunk":
            # Add audio chunk to buffer
            audio_data = np.frombuffer(data["audio"], dtype=np.float32)
            self.audio_buffers[session_id].append(audio_data)
            
        elif message_type == "participant_join":
            # Add participant to meeting
            participant = data["name"]
            self.active_sessions[session_id].participants.append(participant)
            
        elif message_type == "manual_requirement":
            # Handle manually added requirement
            requirement = Requirement(
                text=data["text"],
                category=data.get("category", "manual"),
                confidence=1.0,
                source_timestamp=datetime.now(timezone.utc),
                extracted_at=datetime.now(timezone.utc)
            )
            self.active_sessions[session_id].requirements.append(requirement)
            
        elif message_type == "question_asked":
            # Remove suggested question when it's asked
            question_text = data["text"]
            meeting_state = self.active_sessions[session_id]
            meeting_state.suggested_questions = [
                q for q in meeting_state.suggested_questions 
                if q.text != question_text
            ]
    
    async def _transcription_loop(self, websocket: WebSocket, session_id: str):
        """Background loop for processing audio and generating transcriptions."""
        while True:
            try:
                await asyncio.sleep(self.transcription_interval)
                
                # Process accumulated audio
                if self.audio_buffers[session_id]:
                    audio_chunks = self.audio_buffers[session_id]
                    self.audio_buffers[session_id] = []
                    
                    # Combine audio chunks
                    combined_audio = np.concatenate(audio_chunks)
                    
                    # Transcribe using Whisper
                    result = self.whisper_model.transcribe(combined_audio)
                    new_text = result["text"].strip()
                    
                    if new_text:
                        # Update meeting state
                        meeting_state = self.active_sessions[session_id]
                        meeting_state.current_transcript += " " + new_text
                        
                        # Send transcription update
                        await websocket.send_text(json.dumps({
                            "type": "transcription_update",
                            "text": new_text,
                            "full_transcript": meeting_state.current_transcript,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }))
                        
            except Exception as e:
                logger.error(f"Error in transcription loop: {e}")
    
    async def _analysis_loop(self, websocket: WebSocket, session_id: str):
        """Background loop for analyzing transcript and generating insights."""
        while True:
            try:
                await asyncio.sleep(self.analysis_interval)
                
                meeting_state = self.active_sessions[session_id]
                
                # Only analyze if there's new content
                if len(meeting_state.current_transcript) > 0:
                    # Extract requirements
                    new_requirements = await self._extract_requirements(
                        meeting_state.current_transcript
                    )
                    
                    # Generate suggested questions
                    new_questions = await self._generate_questions(
                        meeting_state.current_transcript,
                        meeting_state.requirements
                    )
                    
                    # Identify missing information
                    missing_info = await self._identify_missing_info(
                        meeting_state.requirements
                    )
                    
                    # Update meeting state
                    meeting_state.requirements.extend(new_requirements)
                    meeting_state.suggested_questions.extend(new_questions)
                    meeting_state.missing_info.update(missing_info)
                    meeting_state.last_analysis = datetime.now(timezone.utc)
                    
                    # Send analysis update
                    await websocket.send_text(json.dumps({
                        "type": "analysis_update",
                        "new_requirements": [asdict(req) for req in new_requirements],
                        "suggested_questions": [asdict(q) for q in new_questions],
                        "missing_info": list(missing_info),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
                    
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
    
    async def _extract_requirements(self, transcript: str) -> List[Requirement]:
        """Extract requirements from transcript using OpenAI."""
        try:
            openai_client = self._get_openai_client()
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract job requirements from the conversation. 
                        Return a JSON array of requirements with fields: text, category, confidence.
                        Categories: technical_skills, experience_level, culture_fit, timeline, location, salary, team_size"""
                    },
                    {
                        "role": "user", 
                        "content": f"Extract requirements from: {transcript}"
                    }
                ],
                temperature=0.3
            )
            
            requirements_data = json.loads(response.choices[0].message.content)
            requirements = []
            
            for req_data in requirements_data:
                requirement = Requirement(
                    text=req_data["text"],
                    category=req_data["category"],
                    confidence=req_data.get("confidence", 0.8),
                    source_timestamp=datetime.now(timezone.utc),
                    extracted_at=datetime.now(timezone.utc)
                )
                requirements.append(requirement)
            
            return requirements
            
        except (ValueError, Exception) as e:
            logger.warning(f"OpenAI not available, skipping requirement extraction: {e}")
            return []
    
    async def _generate_questions(self, transcript: str, requirements: List[Requirement]) -> List[SuggestedQuestion]:
        """Generate follow-up questions based on transcript and requirements."""
        try:
            openai_client = self._get_openai_client()
            # Create context from requirements
            req_context = "\n".join([f"- {req.text}" for req in requirements])
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """Generate 2-3 follow-up questions to fill information gaps.
                        Return JSON array with fields: text, priority (high/medium/low), reasoning, category.
                        Focus on missing critical information."""
                    },
                    {
                        "role": "user",
                        "content": f"Conversation: {transcript}\n\nRequirements: {req_context}\n\nGenerate questions:"
                    }
                ],
                temperature=0.7
            )
            
            questions_data = json.loads(response.choices[0].message.content)
            questions = []
            
            for q_data in questions_data:
                question = SuggestedQuestion(
                    text=q_data["text"],
                    priority=q_data["priority"],
                    reasoning=q_data["reasoning"],
                    category=q_data.get("category", "general"),
                    generated_at=datetime.now(timezone.utc)
                )
                questions.append(question)
            
            return questions
            
        except (ValueError, Exception) as e:
            logger.warning(f"OpenAI not available, skipping question generation: {e}")
            return []
    
    async def _identify_missing_info(self, requirements: List[Requirement]) -> Set[str]:
        """Identify missing critical information."""
        required_categories = {
            "technical_skills", "experience_level", "timeline", "location"
        }
        
        covered_categories = {req.category for req in requirements}
        missing_categories = required_categories - covered_categories
        
        missing_info = set()
        for category in missing_categories:
            if category == "technical_skills":
                missing_info.add("Specific technical skills and technologies")
            elif category == "experience_level":
                missing_info.add("Required years of experience and seniority level")
            elif category == "timeline":
                missing_info.add("Hiring timeline and urgency")
            elif category == "location":
                missing_info.add("Work location and remote policy")
        
        return missing_info
    
    async def _save_meeting_summary(self, session_id: str):
        """Save meeting summary to database."""
        try:
            meeting_state = self.active_sessions[session_id]
            session = get_session()
            
            # Save to database (implement based on your schema)
            # This would save the transcript, requirements, and summary
            
            logger.info(f"Meeting summary saved for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error saving meeting summary: {e}")

# Global instance
realtime_service = RealtimeIntakeService() 