# Real-Time Intake Intelligence System

## 🎯 Overview

The **Real-Time Intake Intelligence System** transforms passive recruitment intake meetings into active AI-assisted sessions. This system provides real-time transcription, requirement extraction, intelligent question generation, and missing information identification during live meetings.

## 🚀 Key Features

### 1. **Real-Time Transcription**
- Live audio streaming using OpenAI Whisper
- WebSocket-based communication for instant updates
- Buffered audio processing for optimal performance

### 2. **Live Requirement Extraction**
- AI-powered requirement identification from conversation
- Automatic categorization (technical skills, experience, culture, etc.)
- Confidence scoring for extracted requirements

### 3. **Intelligent Question Generation**
- Context-aware follow-up questions
- Priority-based question ranking (high/medium/low)
- Reasoning for each suggested question

### 4. **Missing Information Detection**
- Real-time gap analysis
- Critical information alerts
- Actionable insights for recruiters

### 5. **Meeting Assistant Interface**
- Live transcript display
- Real-time requirement tracking
- Suggested questions panel
- Missing information alerts

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   AI Services   │
│                 │    │                  │    │                 │
│ • React UI      │◄──►│ • FastAPI        │◄──►│ • OpenAI GPT    │
│ • WebSocket     │    │ • WebSocket      │    │ • Whisper       │
│ • Audio Capture │    │ • Session Mgmt   │    │ • Embeddings    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 System Components

### Backend Services

#### 1. **RealtimeIntakeService** (`src/github_talent_intelligence/realtime_intake.py`)
- WebSocket connection management
- Audio processing and transcription
- Requirement extraction and analysis
- Question generation and prioritization

#### 2. **API Endpoints** (`src/github_talent_intelligence/api.py`)
- `POST /intake/sessions` - Create new meeting session
- `GET /intake/sessions/{session_id}/summary` - Get meeting summary
- `WS /ws/intake/{session_id}` - WebSocket endpoint

#### 3. **Data Models**
```python
@dataclass
class Requirement:
    text: str
    category: str
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
```

### Frontend Components

#### 1. **IntakeMeeting** (`robot-recruiter-ui/src/pages/IntakeMeeting.tsx`)
- Real-time meeting interface
- Live transcript display
- Requirement management
- Question suggestions
- Audio recording controls

#### 2. **WebSocket Integration**
- Automatic connection management
- Real-time message handling
- Audio streaming
- State synchronization

## 🛠️ Installation & Setup

### Prerequisites
```bash
# Backend dependencies
pip install fastapi uvicorn websockets openai-whisper openai numpy

# Frontend dependencies
cd robot-recruiter-ui
npm install
```

### Environment Variables
```bash
# Required for OpenAI integration
OPENAI_API_KEY=your_openai_api_key_here

# Database configuration
DATABASE_URL=postgresql://user:password@localhost/robot_recruiter
```

### Starting the System

#### 1. **Backend Server**
```bash
cd /Users/paul/Documents/GitHub/Robot-Recruiter
python -m uvicorn src.github_talent_intelligence.api:app --reload --host 0.0.0.0 --port 8000
```

#### 2. **Frontend Development Server**
```bash
cd robot-recruiter-ui
npm run dev
```

#### 3. **Access the Interface**
- Navigate to `http://localhost:5173/intake-meeting`
- Click "Start Recording" to begin audio capture
- Join the meeting as a participant
- Watch real-time transcription and AI insights

## 🧪 Testing & Demo

### Quick Test
```bash
# Run the basic test
python test_realtime_intake.py
```

### Full Demo
```bash
# Run the comprehensive demo
python demo_realtime_intake.py
```

### Manual Testing
1. Start the backend server
2. Open the frontend interface
3. Create a new meeting session
4. Test audio recording and transcription
5. Verify requirement extraction
6. Check question generation

## 📊 Usage Workflow

### 1. **Meeting Setup**
```javascript
// Create new session
const response = await api.post('/intake/sessions');
const { session_id, websocket_url } = response.data;

// Connect WebSocket
const ws = new WebSocket(`ws://localhost:8000${websocket_url}`);
```

### 2. **Audio Processing**
```javascript
// Start recording
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const audioContext = new AudioContext();
const source = audioContext.createMediaStreamSource(stream);

// Send audio chunks
source.connect(processor);
processor.onaudioprocess = (e) => {
  const inputData = e.inputBuffer.getChannelData(0);
  ws.send(JSON.stringify({
    type: 'audio_chunk',
    audio: Array.from(inputData)
  }));
};
```

### 3. **Requirement Management**
```javascript
// Add manual requirement
ws.send(JSON.stringify({
  type: 'manual_requirement',
  text: 'Need senior Python developer',
  category: 'technical_skills'
}));

// Receive extracted requirements
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'analysis_update') {
    console.log('New requirements:', data.new_requirements);
  }
};
```

### 4. **Question Handling**
```javascript
// Ask suggested question
ws.send(JSON.stringify({
  type: 'question_asked',
  text: 'What specific Python frameworks do you need?'
}));

// Receive new questions
if (data.type === 'analysis_update') {
  console.log('Suggested questions:', data.suggested_questions);
}
```

## 🔧 Configuration

### Processing Intervals
```python
# Adjust in RealtimeIntakeService
self.transcription_interval = 3.0  # Process audio every 3 seconds
self.analysis_interval = 5.0       # Analyze transcript every 5 seconds
```

### AI Models
```python
# Whisper model size (base, small, medium, large)
self.whisper_model = whisper.load_model("base")

# OpenAI model for analysis
response = self.openai_client.chat.completions.create(
    model="gpt-3.5-turbo",  # or gpt-4 for better results
    temperature=0.3
)
```

### Requirement Categories
```python
categories = [
    'technical_skills',
    'experience_level', 
    'culture_fit',
    'timeline',
    'location',
    'salary',
    'team_size'
]
```

## 📈 Performance Optimization

### 1. **Audio Processing**
- Use appropriate buffer sizes (4096 samples)
- Implement audio compression for network efficiency
- Consider WebRTC for better audio quality

### 2. **AI Processing**
- Batch process requirements for efficiency
- Cache common question patterns
- Use async processing for non-blocking operations

### 3. **WebSocket Management**
- Implement connection pooling
- Add heartbeat mechanisms
- Handle reconnection gracefully

## 🔒 Security Considerations

### 1. **Audio Privacy**
- Implement end-to-end encryption for audio streams
- Add user consent for audio recording
- Provide clear privacy policies

### 2. **Data Protection**
- Encrypt sensitive meeting data
- Implement session timeouts
- Add user authentication

### 3. **API Security**
- Rate limiting for WebSocket connections
- Input validation for all messages
- CORS configuration for frontend access

## 🐛 Troubleshooting

### Common Issues

#### 1. **WebSocket Connection Failed**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Verify WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws/intake/test
```

#### 2. **Audio Not Recording**
```javascript
// Check browser permissions
navigator.permissions.query({name:'microphone'}).then(result => {
  console.log('Microphone permission:', result.state);
});
```

#### 3. **AI Processing Errors**
```python
# Check OpenAI API key
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
try:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}]
    )
    print("OpenAI API working")
except Exception as e:
    print(f"OpenAI API error: {e}")
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

## 🚀 Future Enhancements

### 1. **Advanced Features**
- Multi-language support
- Speaker identification
- Sentiment analysis
- Meeting summarization

### 2. **Integration**
- Calendar integration (Google Calendar, Outlook)
- Video conferencing platforms (Zoom, Teams)
- CRM systems (Salesforce, HubSpot)

### 3. **Analytics**
- Meeting effectiveness metrics
- Requirement extraction accuracy
- Question quality scoring
- Time-to-hire optimization

## 📚 API Reference

### WebSocket Messages

#### Client → Server
```json
{
  "type": "audio_chunk",
  "audio": [0.1, 0.2, 0.3, ...]
}

{
  "type": "participant_join", 
  "name": "John Doe"
}

{
  "type": "manual_requirement",
  "text": "Need Python developer",
  "category": "technical_skills"
}

{
  "type": "question_asked",
  "text": "What experience level do you need?"
}
```

#### Server → Client
```json
{
  "type": "transcription_update",
  "text": "We need a senior developer",
  "full_transcript": "Complete transcript...",
  "timestamp": "2024-01-01T12:00:00Z"
}

{
  "type": "analysis_update",
  "new_requirements": [...],
  "suggested_questions": [...],
  "missing_info": [...],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### HTTP Endpoints

#### Create Session
```bash
POST /intake/sessions
Response: {"session_id": "uuid", "websocket_url": "/ws/intake/uuid"}
```

#### Get Session Summary
```bash
GET /intake/sessions/{session_id}/summary
Response: {
  "session_id": "uuid",
  "participants": ["John", "Sarah"],
  "duration_minutes": 15.5,
  "requirements_count": 8,
  "questions_generated": 5,
  "missing_info": ["specific salary range"]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🎉 Congratulations!** You now have a complete real-time intake intelligence system that transforms passive meetings into active AI-assisted recruitment sessions. 