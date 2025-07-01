"""
Voice Notes Processing Module
Handles audio upload, transcription, and AI-enhanced suggestions.
"""

import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import whisper
from sqlalchemy.orm import Session

from .db import VoiceNote, Transcription, VoiceEnhancedSuggestion, get_session
from .gpt_stub import get_chatgpt_suggestion


class VoiceNotesProcessor:
    """Process voice notes with transcription and AI enhancement."""
    
    def __init__(self, upload_dir: str = "uploads/voice_notes", whisper_model: str = "base"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_model = whisper_model
        self._model = None
    
    def _load_whisper_model(self):
        """Lazy load Whisper model."""
        if self._model is None:
            self._model = whisper.load_model(self.whisper_model)
        return self._model
    
    def save_audio_file(self, audio_data: bytes, filename: str, user_id: int) -> str:
        """
        Save uploaded audio file to local storage.
        
        Args:
            audio_data: Raw audio bytes
            filename: Original filename
            user_id: ID of the user uploading the file
            
        Returns:
            File path where audio was saved
        """
        # Create user-specific directory
        user_dir = self.upload_dir / str(user_id)
        user_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = Path(filename).suffix
        new_filename = f"{timestamp}_{unique_id}{file_extension}"
        
        file_path = user_dir / new_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        
        return str(file_path)
    
    def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Dictionary with transcription results
        """
        model = self._load_whisper_model()
        
        start_time = time.time()
        result = model.transcribe(audio_file_path)
        processing_time = time.time() - start_time
        
        return {
            'text': result.get('text', '').strip(),
            'language': result.get('language', 'en'),
            'segments': result.get('segments', []),
            'processing_time': processing_time
        }
    
    def create_voice_note(self, 
                         audio_file_path: str, 
                         user_id: int, 
                         feedback_id: Optional[int] = None,
                         file_size: Optional[int] = None,
                         duration: Optional[float] = None) -> VoiceNote:
        """
        Create a voice note record in the database.
        
        Args:
            audio_file_path: Path to saved audio file
            user_id: ID of the user
            feedback_id: Optional feedback ID this voice note relates to
            file_size: Size of audio file in bytes
            duration: Duration of audio in seconds
            
        Returns:
            VoiceNote object
        """
        db = get_session()
        try:
            voice_note = VoiceNote(
                feedback_id=feedback_id,
                user_id=user_id,
                audio_file_path=audio_file_path,
                file_size_bytes=file_size,
                duration_seconds=duration,
                audio_format=Path(audio_file_path).suffix[1:],  # Remove dot
                storage_type="local"
            )
            db.add(voice_note)
            db.commit()
            db.refresh(voice_note)
            return voice_note
        finally:
            db.close()
    
    def save_transcription(self, 
                          voice_note_id: int, 
                          transcription_result: Dict[str, Any]) -> Transcription:
        """
        Save transcription results to database.
        
        Args:
            voice_note_id: ID of the voice note
            transcription_result: Results from Whisper transcription
            
        Returns:
            Transcription object
        """
        db = get_session()
        try:
            transcription = Transcription(
                voice_note_id=voice_note_id,
                text=transcription_result['text'],
                language=transcription_result['language'],
                whisper_model=self.whisper_model,
                processing_time_seconds=transcription_result['processing_time']
            )
            db.add(transcription)
            db.commit()
            db.refresh(transcription)
            return transcription
        finally:
            db.close()
    
    def generate_enhanced_suggestion(self, 
                                   voice_note_id: int,
                                   transcription_text: str,
                                   feedback_context: Optional[str] = None,
                                   temperature: float = 0.2) -> VoiceEnhancedSuggestion:
        """
        Generate enhanced suggestion using ChatGPT with voice context.
        
        Args:
            voice_note_id: ID of the voice note
            transcription_text: Transcribed text from voice note
            feedback_context: Optional context from related feedback
            temperature: ChatGPT temperature setting
            
        Returns:
            VoiceEnhancedSuggestion object
        """
        # Combine transcription with feedback context
        voice_context = f"Voice feedback: {transcription_text}"
        if feedback_context:
            voice_context += f"\n\nFeedback context: {feedback_context}"
        
        # Generate enhanced suggestion
        prompt = f"""
        Based on the following voice feedback, provide an enhanced analysis and suggestion:
        
        {voice_context}
        
        Please provide:
        1. A refined classification or assessment
        2. Key insights from the voice feedback
        3. Recommendations for next steps
        """
        
        enhanced_suggestion = get_chatgpt_suggestion(
            prompt=prompt,
            temperature=temperature
        )
        
        # Save to database
        db = get_session()
        try:
            enhanced = VoiceEnhancedSuggestion(
                voice_note_id=voice_note_id,
                voice_context=voice_context,
                enhanced_suggestion=enhanced_suggestion,
                model="gpt-3.5-turbo",
                temperature=int(temperature * 10)
            )
            db.add(enhanced)
            db.commit()
            db.refresh(enhanced)
            return enhanced
        finally:
            db.close()
    
    def process_voice_note(self, 
                          audio_data: bytes, 
                          filename: str, 
                          user_id: int,
                          feedback_id: Optional[int] = None,
                          temperature: float = 0.2) -> Dict[str, Any]:
        """
        Complete voice note processing pipeline.
        
        Args:
            audio_data: Raw audio bytes
            filename: Original filename
            user_id: ID of the user
            feedback_id: Optional feedback ID
            temperature: ChatGPT temperature setting
            
        Returns:
            Dictionary with processing results
        """
        # 1. Save audio file
        audio_file_path = self.save_audio_file(audio_data, filename, user_id)
        
        # 2. Create voice note record
        voice_note = self.create_voice_note(
            audio_file_path=audio_file_path,
            user_id=user_id,
            feedback_id=feedback_id,
            file_size=len(audio_data)
        )
        
        # 3. Transcribe audio
        transcription_result = self.transcribe_audio(audio_file_path)
        
        # 4. Save transcription
        transcription = self.save_transcription(voice_note.id, transcription_result)
        
        # 5. Get feedback context if available
        feedback_context = None
        if feedback_id:
            db = get_session()
            try:
                from .db import Feedback
                feedback = db.query(Feedback).get(feedback_id)
                if feedback:
                    feedback_context = f"Repo: {feedback.repo_full_name}, Category: {feedback.suggested_category}, Reason: {feedback.reason}"
            finally:
                db.close()
        
        # 6. Generate enhanced suggestion
        enhanced_suggestion = self.generate_enhanced_suggestion(
            voice_note_id=voice_note.id,
            transcription_text=transcription.text,
            feedback_context=feedback_context,
            temperature=temperature
        )
        
        return {
            'voice_note_id': voice_note.id,
            'transcription': transcription.text,
            'language': transcription.language,
            'processing_time': transcription.processing_time_seconds,
            'enhanced_suggestion': enhanced_suggestion.enhanced_suggestion,
            'audio_file_path': audio_file_path
        } 