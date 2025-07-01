"""
Tests for voice notes functionality.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.github_talent_intelligence.voice_notes import VoiceNotesProcessor
from src.github_talent_intelligence.db import get_session, VoiceNote, Transcription, VoiceEnhancedSuggestion, User, Feedback


class TestVoiceNotesProcessor:
    """Test voice notes processing functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create a voice notes processor for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield VoiceNotesProcessor(upload_dir=temp_dir)
    
    @pytest.fixture
    def mock_audio_data(self):
        """Create mock audio data for testing."""
        # Create a simple WAV file header (minimal valid WAV)
        wav_header = (
            b'RIFF' +  # Chunk ID
            (36).to_bytes(4, 'little') +  # Chunk size
            b'WAVE' +  # Format
            b'fmt ' +  # Subchunk1 ID
            (16).to_bytes(4, 'little') +  # Subchunk1 size
            (1).to_bytes(2, 'little') +   # Audio format (PCM)
            (1).to_bytes(2, 'little') +   # Number of channels
            (16000).to_bytes(4, 'little') +  # Sample rate
            (32000).to_bytes(4, 'little') +  # Byte rate
            (2).to_bytes(2, 'little') +   # Block align
            (16).to_bytes(2, 'little') +  # Bits per sample
            b'data' +  # Subchunk2 ID
            (0).to_bytes(4, 'little')     # Subchunk2 size
        )
        return wav_header
    
    def test_save_audio_file(self, processor, mock_audio_data):
        """Test saving audio file to local storage."""
        filename = "test_audio.wav"
        user_id = 123
        
        file_path = processor.save_audio_file(mock_audio_data, filename, user_id)
        
        assert os.path.exists(file_path)
        assert Path(file_path).suffix == '.wav'
        assert str(user_id) in file_path
        
        # Check file content
        with open(file_path, 'rb') as f:
            saved_data = f.read()
        assert saved_data == mock_audio_data
    
    @patch('whisper.load_model')
    def test_transcribe_audio(self, mock_load_model, processor):
        """Test audio transcription with mocked Whisper."""
        # Mock Whisper model and result
        mock_model = Mock()
        mock_result = {
            'text': 'This is a test transcription.',
            'language': 'en',
            'segments': [{'text': 'This is a test transcription.'}]
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'fake audio data')
            temp_file_path = temp_file.name
        
        try:
            result = processor.transcribe_audio(temp_file_path)
            
            assert result['text'] == 'This is a test transcription.'
            assert result['language'] == 'en'
            assert 'processing_time' in result
            assert result['processing_time'] > 0
            
            # Verify Whisper was called
            mock_model.transcribe.assert_called_once_with(temp_file_path)
            
        finally:
            os.unlink(temp_file_path)
    
    def test_create_voice_note(self, processor):
        """Test creating voice note database record."""
        audio_file_path = "/test/path/audio.wav"
        user_id = 123
        feedback_id = 456
        file_size = 1024
        duration = 5.5
        
        # Mock database session
        with patch('src.github_talent_intelligence.voice_notes.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            voice_note = processor.create_voice_note(
                audio_file_path=audio_file_path,
                user_id=user_id,
                feedback_id=feedback_id,
                file_size=file_size,
                duration=duration
            )
            
            # Verify database operations
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()
            mock_session.close.assert_called_once()
            
            # Verify voice note attributes
            assert voice_note.feedback_id == feedback_id
            assert voice_note.user_id == user_id
            assert voice_note.audio_file_path == audio_file_path
            assert voice_note.file_size_bytes == file_size
            assert voice_note.duration_seconds == duration
            assert voice_note.audio_format == 'wav'
            assert voice_note.storage_type == 'local'
    
    @patch('src.github_talent_intelligence.voice_notes.get_chatgpt_suggestion')
    def test_generate_enhanced_suggestion(self, mock_get_suggestion, processor):
        """Test generating enhanced suggestions with voice context."""
        mock_get_suggestion.return_value = "Enhanced suggestion based on voice feedback."
        
        voice_note_id = 123
        transcription_text = "This candidate shows strong technical skills."
        feedback_context = "Repo: test/repo, Category: Backend"
        temperature = 0.3
        
        # Mock database session
        with patch('src.github_talent_intelligence.voice_notes.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            enhanced = processor.generate_enhanced_suggestion(
                voice_note_id=voice_note_id,
                transcription_text=transcription_text,
                feedback_context=feedback_context,
                temperature=temperature
            )
            
            # Verify ChatGPT was called with correct prompt
            mock_get_suggestion.assert_called_once()
            call_args = mock_get_suggestion.call_args
            assert "voice feedback" in call_args[1]['prompt']
            assert transcription_text in call_args[1]['prompt']
            assert feedback_context in call_args[1]['prompt']
            assert call_args[1]['temperature'] == temperature
            
            # Verify database operations
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()
            mock_session.close.assert_called_once()
    
    @patch('src.github_talent_intelligence.voice_notes.get_chatgpt_suggestion')
    @patch('whisper.load_model')
    def test_process_voice_note_pipeline(self, mock_load_model, mock_get_suggestion, processor, mock_audio_data):
        """Test complete voice note processing pipeline."""
        # Mock Whisper
        mock_model = Mock()
        mock_result = {
            'text': 'Test transcription result.',
            'language': 'en',
            'segments': []
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        # Mock ChatGPT
        mock_get_suggestion.return_value = "Enhanced suggestion from voice feedback."
        
        # Mock database sessions
        with patch('src.github_talent_intelligence.voice_notes.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            # Mock feedback query
            mock_feedback = Mock()
            mock_feedback.repo_full_name = "test/repo"
            mock_feedback.suggested_category = "Backend"
            mock_feedback.reason = "Strong technical skills"
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_feedback
            
            result = processor.process_voice_note(
                audio_data=mock_audio_data,
                filename="test_audio.wav",
                user_id=123,
                feedback_id=456,
                temperature=0.2
            )
            
            # Verify result structure
            assert 'voice_note_id' in result
            assert 'transcription' in result
            assert 'language' in result
            assert 'processing_time' in result
            assert 'enhanced_suggestion' in result
            assert 'audio_file_path' in result
            
            assert result['transcription'] == 'Test transcription result.'
            assert result['language'] == 'en'
            assert result['enhanced_suggestion'] == 'Enhanced suggestion from voice feedback.'


class TestVoiceNotesAPI:
    """Test voice notes API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from src.github_talent_intelligence.api import app
        return TestClient(app)
    
    def test_upload_voice_note_success(self, client):
        """Test successful voice note upload."""
        # This would require more complex setup with actual file upload
        # and database mocking. For now, we'll test the basic structure.
        pass
    
    def test_get_voice_note(self, client):
        """Test retrieving voice note details."""
        # Mock database query
        with patch('src.github_talent_intelligence.api.get_session') as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            
            # Mock voice note
            mock_voice_note = Mock()
            mock_voice_note.id = 123
            mock_voice_note.audio_file_path = "/test/path/audio.wav"
            mock_voice_note.file_size_bytes = 1024
            mock_voice_note.duration_seconds = 5.5
            mock_voice_note.audio_format = "wav"
            mock_voice_note.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_voice_note.feedback_id = 456
            
            mock_session.query.return_value.get.return_value = mock_voice_note
            
            # Mock transcription
            mock_transcription = Mock()
            mock_transcription.text = "Test transcription"
            mock_transcription.language = "en"
            mock_transcription.confidence_score = 0.95
            mock_transcription.processing_time_seconds = 1.2
            
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_transcription
            
            # Mock enhanced suggestions
            mock_suggestion = Mock()
            mock_suggestion.id = 789
            mock_suggestion.enhanced_suggestion = "Enhanced suggestion"
            mock_suggestion.ai_analysis = "AI analysis"
            mock_suggestion.model = "gpt-3.5-turbo"
            mock_suggestion.temperature = 2
            mock_suggestion.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            
            mock_session.query.return_value.filter_by.return_value.all.return_value = [mock_suggestion]
            
            response = client.get("/voice-notes/123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["voice_note"]["id"] == 123
            assert data["transcription"]["text"] == "Test transcription"
            assert len(data["enhanced_suggestions"]) == 1 