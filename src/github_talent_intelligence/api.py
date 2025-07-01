from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path

from .talent_intelligence import TalentAnalyzer
from .candidate_db import DatabaseManager, CandidateProfile
from .recruiting import RecruitingIntegration
from .db import Feedback, User, get_session
from .gpt_stub import get_chatgpt_suggestion
from .voice_notes import VoiceNotesProcessor

app = FastAPI(title="Robot Recruiter API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
analyzer = TalentAnalyzer()
db_manager = DatabaseManager("sqlite:///robot_recruiter.db")
recruiting_engine = RecruitingIntegration()

# Pydantic models
class RepositoryAnalysisRequest(BaseModel):
    repo_url: str
    analysis_type: str = "full"

class AnalysisResponse(BaseModel):
    session_id: str
    status: str
    message: str

class CandidateResponse(BaseModel):
    id: str
    username: str
    name: Optional[str]
    email: Optional[str]
    location: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    blog: Optional[str]
    twitter_username: Optional[str]
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: Optional[str]
    updated_at: Optional[str]
    classification: Optional[Dict[str, Any]]
    skills: List[str]
    experience_level: Optional[str]
    availability: Optional[str]
    contact_info: Optional[Dict[str, Any]]

class RepositoryResponse(BaseModel):
    id: str
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    created_at: Optional[str]
    updated_at: Optional[str]
    analysis_status: str

class DashboardStats(BaseModel):
    total_candidates: int
    total_repositories: int
    analysis_sessions: int
    top_skills: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

class FeedbackRequest(BaseModel):
    user_email: str
    repo_full_name: str
    suggested_category: str
    reason: str

class ChatGPTSuggestionRequest(BaseModel):
    feedback_id: int
    temperature: float = 0.2

class VoiceNoteResponse(BaseModel):
    voice_note_id: int
    transcription: str
    language: str
    processing_time: float
    enhanced_suggestion: str
    audio_file_path: str

# Initialize voice notes processor
voice_processor = VoiceNotesProcessor()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Robot Recruiter API is running"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_repository(request: RepositoryAnalysisRequest, background_tasks: BackgroundTasks):
    """Start repository analysis in background"""
    try:
        # Generate session ID
        session_id = f"session_{int(os.urandom(4).hex(), 16)}"
        
        # Start analysis in background
        background_tasks.add_task(run_analysis, session_id, request.repo_url, request.analysis_type)
        
        return AnalysisResponse(
            session_id=session_id,
            status="started",
            message="Analysis started successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_analysis(session_id: str, repo_url: str, analysis_type: str):
    """Background task to run repository analysis"""
    try:
        # Run the analysis
        results = analyzer.analyze_repository(repo_url, analysis_type)
        
        # Save results to database
        # This would integrate with your existing analysis pipeline
        
        print(f"Analysis completed for session {session_id}")
    except Exception as e:
        print(f"Analysis failed for session {session_id}: {e}")

@app.get("/analysis/{session_id}")
async def get_analysis_status(session_id: str):
    """Get analysis status and results"""
    # This would check the actual analysis status
    # For now, return mock data
    return {
        "session_id": session_id,
        "status": "completed",
        "progress": 100,
        "results": {
            "contributors_count": 25,
            "repositories_analyzed": 1,
            "candidates_found": 15
        }
    }

@app.get("/candidates", response_model=List[CandidateResponse])
async def get_candidates(skip: int = 0, limit: int = 100, classification: Optional[str] = None):
    """Get candidates with optional filtering"""
    try:
        candidates = db_manager.get_candidate_profiles(limit=limit, offset=skip)
        return [
            CandidateResponse(
                id=str(candidate.id),
                username=candidate.login,
                name=candidate.name,
                email=candidate.email,
                location=candidate.location,
                bio=candidate.bio,
                company=candidate.company,
                blog=candidate.blog,
                twitter_username=candidate.twitter_username,
                public_repos=candidate.public_repos or 0,
                public_gists=candidate.public_gists or 0,
                followers=candidate.followers or 0,
                following=candidate.following or 0,
                created_at=candidate.last_updated.isoformat() if candidate.last_updated else None,
                updated_at=candidate.last_updated.isoformat() if candidate.last_updated else None,
                classification=candidate.primary_classifications,
                skills=candidate.top_skills or [],
                experience_level=None,
                availability=None,
                contact_info=None
            )
            for candidate in candidates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    """Get specific candidate details"""
    try:
        # This would fetch from your candidate database
        raise HTTPException(status_code=404, detail="Candidate not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/candidates/search")
async def search_candidates(filters: Dict[str, Any]):
    """Search candidates with advanced filters"""
    try:
        results = db_manager.search_candidates(**filters)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories", response_model=List[RepositoryResponse])
async def get_repositories(skip: int = 0, limit: int = 100):
    """Get analyzed repositories"""
    try:
        # This would fetch from your repository database
        # For now, return mock data
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str):
    """Get specific repository details"""
    try:
        # This would fetch from your repository database
        raise HTTPException(status_code=404, detail="Repository not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis-sessions")
async def get_analysis_sessions():
    """Get all analysis sessions"""
    try:
        # This would fetch from your sessions database
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis-sessions/{session_id}")
async def get_analysis_session(session_id: str):
    """Get specific analysis session"""
    try:
        # This would fetch from your sessions database
        return {
            "session_id": session_id,
            "status": "completed",
            "created_at": "2024-01-01T00:00:00Z",
            "results": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get candidate count - this would need to be implemented
        total_candidates = 0  # db_manager.get_candidate_count()
        
        return DashboardStats(
            total_candidates=total_candidates,
            total_repositories=0,  # Would fetch from repo database
            analysis_sessions=0,   # Would fetch from sessions database
            top_skills=[
                {"skill": "Python", "count": 45},
                {"skill": "JavaScript", "count": 32},
                {"skill": "React", "count": 28}
            ],
            recent_activity=[
                {"type": "analysis", "message": "Analyzed chipsalliance/Caliptra", "timestamp": "2024-01-01T10:00:00Z"},
                {"type": "candidate", "message": "Added 15 new candidates", "timestamp": "2024-01-01T09:30:00Z"}
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/analytics")
async def get_analytics(timeframe: str = "30d"):
    """Get analytics data"""
    try:
        # This would generate analytics based on your data
        return {
            "candidates_over_time": [],
            "skills_distribution": [],
            "top_repositories": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    db = get_session()
    user = db.query(User).filter_by(email=feedback.user_email).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found. Please add the user first.")
    fb = Feedback(
        repo_full_name=feedback.repo_full_name,
        suggested_category=feedback.suggested_category,
        reason=feedback.reason,
        user_id=user.id
    )
    db.add(fb)
    db.commit()
    db.close()
    return {"status": "success", "message": f"Feedback submitted for {feedback.repo_full_name}."}

@app.get("/feedback")
async def get_feedback():
    db = get_session()
    feedbacks = db.query(Feedback).all()
    results = []
    for fb in feedbacks:
        user = db.query(User).get(fb.user_id)
        results.append({
            "repo_full_name": fb.repo_full_name,
            "suggested_category": fb.suggested_category,
            "reason": fb.reason,
            "user_email": user.email if user else None,
            "status": fb.status
        })
    db.close()
    return results

@app.post("/chatgpt/suggestion")
async def generate_chatgpt_suggestion(request: ChatGPTSuggestionRequest):
    db = get_session()
    feedback = db.query(Feedback).get(request.feedback_id)
    db.close()
    if not feedback:
        raise HTTPException(status_code=404, detail=f"Feedback with ID {request.feedback_id} not found.")
    prompt = f"Classify the following GitHub repository into one of the categories.\nRepo: {feedback.repo_full_name}\nSuggested category: {feedback.suggested_category}\nReason: {feedback.reason}"
    response = get_chatgpt_suggestion(prompt, feedback_id=request.feedback_id, temperature=request.temperature)
    return {"suggestion": response}

@app.post("/voice-notes/upload", response_model=VoiceNoteResponse)
async def upload_voice_note(
    audio_file: UploadFile = File(...),
    feedback_id: Optional[int] = Form(None),
    user_email: str = Form(...),
    temperature: float = Form(0.2)
):
    """Upload and process a voice note."""
    try:
        # Validate user
        db = get_session()
        user = db.query(User).filter_by(email=user_email).first()
        if not user:
            db.close()
            raise HTTPException(status_code=404, detail="User not found")
        db.close()
        
        # Validate file type
        allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        file_extension = Path(audio_file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read audio data
        audio_data = await audio_file.read()
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Process voice note
        result = voice_processor.process_voice_note(
            audio_data=audio_data,
            filename=audio_file.filename,
            user_id=user.id,
            feedback_id=feedback_id,
            temperature=temperature
        )
        
        return VoiceNoteResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice note processing failed: {str(e)}")

@app.get("/voice-notes/{voice_note_id}")
async def get_voice_note(voice_note_id: int):
    """Get voice note details including transcription and enhanced suggestion."""
    db = get_session()
    try:
        from .db import VoiceNote, Transcription, VoiceEnhancedSuggestion
        
        voice_note = db.query(VoiceNote).get(voice_note_id)
        if not voice_note:
            raise HTTPException(status_code=404, detail="Voice note not found")
        
        # Get transcription
        transcription = db.query(Transcription).filter_by(voice_note_id=voice_note_id).first()
        
        # Get enhanced suggestions
        enhanced_suggestions = db.query(VoiceEnhancedSuggestion).filter_by(voice_note_id=voice_note_id).all()
        
        return {
            "voice_note": {
                "id": voice_note.id,
                "audio_file_path": voice_note.audio_file_path,
                "file_size_bytes": voice_note.file_size_bytes,
                "duration_seconds": voice_note.duration_seconds,
                "audio_format": voice_note.audio_format,
                "created_at": voice_note.created_at.isoformat(),
                "feedback_id": voice_note.feedback_id
            },
            "transcription": {
                "text": transcription.text if transcription else None,
                "language": transcription.language if transcription else None,
                "confidence_score": transcription.confidence_score if transcription else None,
                "processing_time": transcription.processing_time_seconds if transcription else None
            },
            "enhanced_suggestions": [
                {
                    "id": suggestion.id,
                    "enhanced_suggestion": suggestion.enhanced_suggestion,
                    "ai_analysis": suggestion.ai_analysis,
                    "model": suggestion.model,
                    "temperature": suggestion.temperature / 10,  # Convert back to float
                    "created_at": suggestion.created_at.isoformat()
                }
                for suggestion in enhanced_suggestions
            ]
        }
    finally:
        db.close()

@app.get("/voice-notes/feedback/{feedback_id}")
async def get_voice_notes_for_feedback(feedback_id: int):
    """Get all voice notes for a specific feedback item."""
    db = get_session()
    try:
        from .db import VoiceNote, Transcription, VoiceEnhancedSuggestion
        
        voice_notes = db.query(VoiceNote).filter_by(feedback_id=feedback_id).all()
        
        results = []
        for voice_note in voice_notes:
            transcription = db.query(Transcription).filter_by(voice_note_id=voice_note.id).first()
            enhanced_suggestions = db.query(VoiceEnhancedSuggestion).filter_by(voice_note_id=voice_note.id).all()
            
            results.append({
                "voice_note_id": voice_note.id,
                "audio_file_path": voice_note.audio_file_path,
                "created_at": voice_note.created_at.isoformat(),
                "transcription": transcription.text if transcription else None,
                "enhanced_suggestions_count": len(enhanced_suggestions)
            })
        
        return {"voice_notes": results}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 