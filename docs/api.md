# Api

Documentation for this section.

## POST /chatgpt/suggestion

Generate a ChatGPT suggestion for a feedback item.

**Request Body:**
```
{
  "feedback_id": 123,
  "temperature": 0.2 // optional, default 0.2
}
```

**Response:**
```
{
  "suggestion": "..."
}
```

- `temperature` controls the randomness/creativity of the response (0.2 = focused, 1.0 = creative).
- Returns the generated suggestion as a string.

**Example:**
```
curl -X POST http://localhost:8000/chatgpt/suggestion \
  -H "Content-Type: application/json" \
  -d '{"feedback_id": 123, "temperature": 0.2}'
```

## POST /voice-notes/upload

Upload and process a voice note with automatic transcription and AI enhancement.

**Request:** Multipart form data
- `audio_file`: Audio file (WAV, MP3, M4A, FLAC, OGG)
- `feedback_id`: Optional feedback ID to link voice note
- `user_email`: User's email address
- `temperature`: Optional ChatGPT temperature (default: 0.2)

**Response:**
```json
{
  "voice_note_id": 123,
  "transcription": "This candidate shows strong technical skills...",
  "language": "en",
  "processing_time": 1.2,
  "enhanced_suggestion": "Based on the voice feedback...",
  "audio_file_path": "/uploads/voice_notes/123/20240101_120000_abc123.wav"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/voice-notes/upload \
  -F "audio_file=@feedback.wav" \
  -F "feedback_id=456" \
  -F "user_email=reviewer@example.com" \
  -F "temperature=0.3"
```

## GET /voice-notes/{voice_note_id}

Get detailed information about a specific voice note.

**Response:**
```json
{
  "voice_note": {
    "id": 123,
    "audio_file_path": "/uploads/voice_notes/123/audio.wav",
    "file_size_bytes": 1024000,
    "duration_seconds": 15.5,
    "audio_format": "wav",
    "created_at": "2024-01-01T12:00:00Z",
    "feedback_id": 456
  },
  "transcription": {
    "text": "This candidate shows strong technical skills...",
    "language": "en",
    "confidence_score": 0.95,
    "processing_time": 1.2
  },
  "enhanced_suggestions": [
    {
      "id": 789,
      "enhanced_suggestion": "Based on the voice feedback...",
      "ai_analysis": "Additional AI insights...",
      "model": "gpt-3.5-turbo",
      "temperature": 0.2,
      "created_at": "2024-01-01T12:01:00Z"
    }
  ]
}
```

## GET /voice-notes/feedback/{feedback_id}

Get all voice notes associated with a specific feedback item.

**Response:**
```json
{
  "voice_notes": [
    {
      "voice_note_id": 123,
      "audio_file_path": "/uploads/voice_notes/123/audio.wav",
      "created_at": "2024-01-01T12:00:00Z",
      "transcription": "This candidate shows strong technical skills...",
      "enhanced_suggestions_count": 1
    }
  ]
}
```

## Voice Notes Processing Pipeline

1. **Audio Upload**: User uploads audio file via API
2. **File Storage**: Audio saved to local storage with unique filename
3. **Transcription**: Whisper AI transcribes audio to text
4. **Context Enhancement**: Transcription combined with feedback context
5. **AI Analysis**: ChatGPT generates enhanced suggestions
6. **Database Storage**: All results stored with relationships

**Supported Audio Formats:**
- WAV, MP3, M4A, FLAC, OGG

**Whisper Models:**
- **Base model** (default): Good balance of speed and accuracy
- **Tiny model**: Fastest, lower accuracy
- **Small model**: Higher accuracy, slower processing

**Storage:**
- **Local storage** (default): Files stored in `uploads/voice_notes/`
- **Cloud storage**: Configurable for scalability
