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

## Review Workflow Endpoints

### POST /review-sessions

Create a new review session for batch processing feedback items.

**Request Body:**
```json
{
  "name": "Q1 2024 Backend Reviews",
  "reviewer_email": "senior.reviewer@company.com",
  "description": "Review backend candidates for Q1 hiring",
  "target_days": 14
}
```

**Response:**
```json
{
  "session_id": 1,
  "name": "Q1 2024 Backend Reviews",
  "reviewer_id": 123,
  "status": "active",
  "created_at": "2024-01-01T10:00:00Z",
  "target_completion_date": "2024-01-15T10:00:00Z"
}
```

### POST /assignments

Assign feedback items to reviewers.

**Request Body:**
```json
{
  "feedback_id": 456,
  "reviewer_email": "reviewer@company.com",
  "session_id": 1,
  "priority": "high",
  "due_days": 3,
  "notes": "Urgent review needed for senior position"
}
```

**Response:**
```json
{
  "assignment_id": 789,
  "feedback_id": 456,
  "reviewer_id": 123,
  "priority": "high",
  "status": "assigned",
  "assigned_at": "2024-01-01T10:00:00Z",
  "due_date": "2024-01-04T10:00:00Z"
}
```

### GET /assignments/reviewer/{reviewer_email}

Get all assignments for a specific reviewer.

**Query Parameters:**
- `status`: Filter by assignment status (assigned, in_review, completed, overdue)

**Response:**
```json
{
  "assignments": [
    {
      "assignment_id": 789,
      "feedback_id": 456,
      "repo_full_name": "company/backend-service",
      "suggested_category": "Backend",
      "priority": "high",
      "status": "assigned",
      "assigned_at": "2024-01-01T10:00:00Z",
      "due_date": "2024-01-04T10:00:00Z",
      "is_overdue": false,
      "voice_notes_count": 2,
      "notes": "Urgent review needed"
    }
  ]
}
```

### PUT /assignments/{assignment_id}

Update assignment status.

**Request Body:**
```json
{
  "status": "in_review",
  "notes": "Started reviewing the candidate"
}
```

**Response:**
```json
{
  "assignment_id": 789,
  "status": "in_review",
  "notes": "Started reviewing the candidate"
}
```

### POST /reviews/submit

Submit a review decision for a feedback item.

**Request Body:**
```json
{
  "feedback_id": 456,
  "reviewer_email": "reviewer@company.com",
  "decision": "approved",
  "notes": "Strong technical skills, good communication",
  "voice_note_id": 123
}
```

**Response:**
```json
{
  "feedback_id": 456,
  "status": "approved",
  "review_notes": "Strong technical skills, good communication",
  "reviewed_at": "2024-01-01T15:30:00Z",
  "reviewed_by": 123
}
```

### GET /review-sessions/{session_id}/summary

Get summary statistics for a review session.

**Response:**
```json
{
  "session_id": 1,
  "session_name": "Q1 2024 Backend Reviews",
  "reviewer_id": 123,
  "status": "active",
  "created_at": "2024-01-01T10:00:00Z",
  "target_completion_date": "2024-01-15T10:00:00Z",
  "statistics": {
    "total_assignments": 25,
    "completed": 18,
    "in_review": 5,
    "overdue": 2,
    "completion_rate": 72.0
  },
  "feedback_statuses": {
    "approved": 12,
    "rejected": 4,
    "needs_revision": 2
  }
}
```

### GET /reviewers/{reviewer_email}/performance

Get performance statistics for a reviewer.

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
  "reviewer_id": 123,
  "period_days": 30,
  "total_completed": 45,
  "avg_completion_time_hours": 4.2,
  "decision_breakdown": {
    "approved": 28,
    "rejected": 12,
    "needs_revision": 5
  }
}
```

### POST /assignments/auto-assign

Automatically assign pending feedback to a reviewer.

**Query Parameters:**
- `reviewer_email`: Email of the reviewer
- `max_assignments`: Maximum assignments to create (default: 10)

**Response:**
```json
{
  "reviewer_email": "reviewer@company.com",
  "assignments_created": 8,
  "assignments": [
    {
      "assignment_id": 789,
      "feedback_id": 456,
      "repo_full_name": "company/backend-service"
    }
  ]
}
```

### GET /feedback/{feedback_id}/review-history

Get complete review history for a feedback item.

**Response:**
```json
{
  "feedback_id": 456,
  "assignments": [
    {
      "assignment_id": 789,
      "reviewer_id": 123,
      "status": "completed",
      "assigned_at": "2024-01-01T10:00:00Z",
      "due_date": "2024-01-04T10:00:00Z",
      "priority": "high",
      "notes": "Urgent review needed"
    }
  ],
  "voice_notes": [
    {
      "voice_note_id": 123,
      "user_id": 123,
      "created_at": "2024-01-01T15:30:00Z",
      "transcription": "This candidate shows excellent problem-solving skills...",
      "audio_file_path": "/uploads/voice_notes/123/audio.wav"
    }
  ]
}
```

## Review Workflow States

### Assignment Statuses
- **assigned**: Feedback assigned to reviewer
- **in_review**: Reviewer is actively reviewing
- **completed**: Review completed, decision submitted
- **overdue**: Past due date, not completed

### Feedback Statuses
- **pending**: Awaiting review
- **assigned**: Assigned to reviewer
- **in_review**: Under review
- **approved**: Review approved
- **rejected**: Review rejected
- **needs_revision**: Requires changes/revision

### Review Decisions
- **approved**: Candidate approved for next stage
- **rejected**: Candidate rejected
- **needs_revision**: Requires additional information or changes

## Priority Levels
- **low**: Low priority, can be reviewed later
- **normal**: Standard priority
- **high**: High priority, review soon
- **urgent**: Critical priority, immediate attention needed
