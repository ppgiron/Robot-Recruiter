from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, APIRouter, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .talent_intelligence import TalentAnalyzer
from .candidate_db import DatabaseManager, CandidateProfile
from .recruiting import RecruitingIntegration
from .db import Feedback, User, get_session
from .gpt_stub import get_chatgpt_suggestion
from .voice_notes import VoiceNotesProcessor
from .review_workflow import ReviewWorkflowManager
from .embedding_service import embedding_service
from .realtime_intake import realtime_service
from sqlalchemy import text
from .continuous_learning import continuous_learning, FeedbackData, FeedbackType, FeedbackSource

# Set up logging
logger = logging.getLogger(__name__)

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

# Session store for analysis results
analysis_sessions = {}

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

class ReviewSessionRequest(BaseModel):
    name: str
    reviewer_email: str
    description: Optional[str] = None
    target_days: Optional[int] = None

class AssignmentRequest(BaseModel):
    feedback_id: int
    reviewer_email: str
    session_id: Optional[int] = None
    priority: str = "normal"
    due_days: Optional[int] = None
    notes: Optional[str] = None

class ReviewSubmissionRequest(BaseModel):
    feedback_id: int
    reviewer_email: str
    decision: str  # approved, rejected, needs_revision
    notes: Optional[str] = None
    voice_note_id: Optional[int] = None

# Initialize voice notes processor
voice_processor = VoiceNotesProcessor()

# Initialize workflow manager
workflow_manager = ReviewWorkflowManager()

router = APIRouter()

@router.post("/semantic-search/candidates")
def semantic_search_candidates(
    payload: dict = Body(..., example={"query": "backend engineer distributed systems", "top_k": 10})
):
    """
    Semantic search for candidates using vector similarity.
    Request body: {"query": str, "top_k": int (optional)}
    Returns: List of candidates with similarity scores.
    """
    query = payload.get("query")
    top_k = payload.get("top_k", 10)
    if not query:
        raise HTTPException(status_code=400, detail="Missing query string.")
    try:
        query_emb = embedding_service.generate_embedding(query)
        # Convert numpy array to list of floats for PostgreSQL
        query_emb_list = [float(x) for x in query_emb]
        session = get_session()
        # Use raw SQL for pgvector cosine search with explicit vector construction
        vector_str = '[' + ','.join(map(str, query_emb_list)) + ']'
        sql = text(f'''
            SELECT candidate_id, 1 - (embedding <#> '{vector_str}'::vector) AS similarity
            FROM candidate_embeddings
            ORDER BY embedding <#> '{vector_str}'::vector
            LIMIT :top_k
        ''')
        results = session.execute(sql, {"top_k": top_k}).fetchall()
        candidates = []
        for row in results:
            candidate = session.query(CandidateProfile).get(row.candidate_id)
            if candidate:
                candidates.append({
                    "id": str(candidate.id),
                    "login": candidate.login,
                    "name": candidate.name,
                    "location": candidate.location,
                    "bio": candidate.bio,
                    "skills": candidate.top_skills,
                    "similarity": float(row.similarity)
                })
        return {"results": candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {e}")

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
        # Initialize session
        analysis_sessions[session_id] = {
            "status": "running",
            "progress": 0,
            "started_at": datetime.now(timezone.utc),
            "results": None,
            "error": None
        }
        
        # Run the analysis
        repositories = analyzer.analyze_repository(repo_url, analysis_type)
        
        if not repositories:
            raise Exception("No repositories found or analysis failed")
        
        repo = repositories[0]  # We're analyzing a single repository
        
        # Calculate results
        contributors_count = len(repo.contributors)
        candidates_found = len([c for c in repo.contributors if c.expertise_score and c.expertise_score > 0.3])
        
        # Store results
        analysis_sessions[session_id] = {
            "status": "completed",
            "progress": 100,
            "started_at": analysis_sessions[session_id]["started_at"],
            "completed_at": datetime.now(timezone.utc),
            "results": {
                "contributors_count": contributors_count,
                "repositories_analyzed": 1,
                "candidates_found": candidates_found,
                "repository": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "classification": repo.classification,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "contributors": [
                        {
                            "login": c.login,
                            "name": c.name,
                            "contributions": c.contributions,
                            "expertise_score": c.expertise_score,
                            "skills": c.skills or [],
                            "location": c.location,
                            "company": c.company
                        }
                        for c in repo.contributors
                    ]
                }
            },
            "error": None
        }
        
        print(f"Analysis completed for session {session_id}")
        
    except Exception as e:
        print(f"Analysis failed for session {session_id}: {e}")
        analysis_sessions[session_id] = {
            "status": "failed",
            "progress": 0,
            "started_at": analysis_sessions.get(session_id, {}).get("started_at", datetime.now(timezone.utc)),
            "completed_at": datetime.now(timezone.utc),
            "results": None,
            "error": str(e)
        }

@app.get("/analysis/{session_id}")
async def get_analysis_status(session_id: str):
    """Get analysis status and results"""
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    session_data = analysis_sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": session_data["status"],
        "progress": session_data["progress"],
        "started_at": session_data["started_at"].isoformat(),
        "completed_at": session_data["completed_at"].isoformat() if session_data["completed_at"] else None,
        "error": session_data["error"],
        "results": session_data["results"]
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

@app.post("/review-sessions")
async def create_review_session(request: ReviewSessionRequest):
    """Create a new review session."""
    try:
        db = get_session()
        reviewer = db.query(User).filter_by(email=request.reviewer_email).first()
        if not reviewer:
            db.close()
            raise HTTPException(status_code=404, detail="Reviewer not found")
        db.close()
        
        # Calculate target date
        target_date = None
        if request.target_days:
            from datetime import datetime, timedelta
            target_date = datetime.now() + timedelta(days=request.target_days)
        
        session = workflow_manager.create_review_session(
            name=request.name,
            reviewer_id=reviewer.id,
            description=request.description,
            target_completion_date=target_date
        )
        
        return {
            "session_id": session.id,
            "name": session.name,
            "reviewer_id": session.reviewer_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "target_completion_date": session.target_completion_date.isoformat() if session.target_completion_date else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review session: {str(e)}")

@app.post("/assignments")
async def assign_feedback(request: AssignmentRequest):
    """Assign feedback to a reviewer."""
    try:
        db = get_session()
        reviewer = db.query(User).filter_by(email=request.reviewer_email).first()
        if not reviewer:
            db.close()
            raise HTTPException(status_code=404, detail="Reviewer not found")
        db.close()
        
        # Calculate due date
        due_date = None
        if request.due_days:
            from datetime import datetime, timedelta
            due_date = datetime.now() + timedelta(days=request.due_days)
        
        assignment = workflow_manager.assign_feedback_to_reviewer(
            feedback_id=request.feedback_id,
            reviewer_id=reviewer.id,
            review_session_id=request.session_id,
            priority=request.priority,
            due_date=due_date,
            notes=request.notes
        )
        
        return {
            "assignment_id": assignment.id,
            "feedback_id": assignment.feedback_id,
            "reviewer_id": assignment.reviewer_id,
            "priority": assignment.priority,
            "status": assignment.status,
            "assigned_at": assignment.assigned_at.isoformat(),
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign feedback: {str(e)}")

@app.get("/assignments/reviewer/{reviewer_email}")
async def get_reviewer_assignments(reviewer_email: str, status: Optional[str] = None):
    """Get assignments for a reviewer."""
    try:
        db = get_session()
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            db.close()
            raise HTTPException(status_code=404, detail="Reviewer not found")
        db.close()
        
        assignments = workflow_manager.get_reviewer_assignments(
            reviewer_id=reviewer.id,
            status=status
        )
        
        return {"assignments": assignments}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assignments: {str(e)}")

@app.put("/assignments/{assignment_id}")
async def update_assignment(assignment_id: int, status: str, notes: Optional[str] = None):
    """Update assignment status."""
    try:
        assignment = workflow_manager.update_assignment_status(
            assignment_id=assignment_id,
            status=status,
            notes=notes
        )
        
        return {
            "assignment_id": assignment.id,
            "status": assignment.status,
            "notes": assignment.notes
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update assignment: {str(e)}")

@app.post("/reviews/submit")
async def submit_review(request: ReviewSubmissionRequest):
    """Submit a review decision."""
    try:
        db = get_session()
        reviewer = db.query(User).filter_by(email=request.reviewer_email).first()
        if not reviewer:
            db.close()
            raise HTTPException(status_code=404, detail="Reviewer not found")
        db.close()
        
        feedback = workflow_manager.submit_review(
            feedback_id=request.feedback_id,
            reviewer_id=reviewer.id,
            review_decision=request.decision,
            review_notes=request.notes,
            voice_note_id=request.voice_note_id
        )
        
        return {
            "feedback_id": feedback.id,
            "status": feedback.status,
            "review_notes": feedback.review_notes,
            "reviewed_at": feedback.reviewed_at.isoformat(),
            "reviewed_by": feedback.reviewed_by
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")

@app.get("/review-sessions/{session_id}/summary")
async def get_session_summary(session_id: int):
    """Get summary statistics for a review session."""
    try:
        summary = workflow_manager.get_review_session_summary(session_id)
        return summary
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session summary: {str(e)}")

@app.get("/reviewers/{reviewer_email}/performance")
async def get_reviewer_performance(reviewer_email: str, days: int = 30):
    """Get performance statistics for a reviewer."""
    try:
        db = get_session()
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            db.close()
            raise HTTPException(status_code=404, detail="Reviewer not found")
        db.close()
        
        stats = workflow_manager.get_reviewer_performance_stats(reviewer.id, days)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@app.post("/assignments/auto-assign")
async def auto_assign_feedback(reviewer_email: str, max_assignments: int = 10):
    """Automatically assign pending feedback to a reviewer."""
    try:
        db = get_session()
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            db.close()
            raise HTTPException(status_code=404, detail="Reviewer not found")
        db.close()
        
        assignments = workflow_manager.auto_assign_pending_feedback(
            reviewer_id=reviewer.id,
            max_assignments=max_assignments
        )
        
        return {
            "reviewer_email": reviewer_email,
            "assignments_created": len(assignments),
            "assignments": [
                {
                    "assignment_id": a.id,
                    "feedback_id": a.feedback_id,
                    "repo_full_name": a.feedback.repo_full_name
                }
                for a in assignments
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-assign feedback: {str(e)}")

@app.get("/feedback/{feedback_id}/review-history")
async def get_feedback_review_history(feedback_id: int):
    """Get review history for a feedback item."""
    db = get_session()
    try:
        from .db import ReviewAssignment, VoiceNote, Transcription
        
        # Get assignments
        assignments = db.query(ReviewAssignment).filter_by(feedback_id=feedback_id).all()
        
        # Get voice notes
        voice_notes = db.query(VoiceNote).filter_by(feedback_id=feedback_id).all()
        
        history = {
            "feedback_id": feedback_id,
            "assignments": [],
            "voice_notes": []
        }
        
        for assignment in assignments:
            history["assignments"].append({
                "assignment_id": assignment.id,
                "reviewer_id": assignment.reviewer_id,
                "status": assignment.status,
                "assigned_at": assignment.assigned_at.isoformat(),
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "priority": assignment.priority,
                "notes": assignment.notes
            })
        
        for voice_note in voice_notes:
            transcription = db.query(Transcription).filter_by(voice_note_id=voice_note.id).first()
            history["voice_notes"].append({
                "voice_note_id": voice_note.id,
                "user_id": voice_note.user_id,
                "created_at": voice_note.created_at.isoformat(),
                "transcription": transcription.text if transcription else None,
                "audio_file_path": voice_note.audio_file_path
            })
        
        return history
        
    finally:
        db.close()

# ============================================================================
# REAL-TIME INTAKE INTELLIGENCE ENDPOINTS
# ============================================================================

@app.websocket("/ws/intake/{session_id}")
async def websocket_intake_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time intake meetings"""
    await realtime_service.handle_websocket(websocket, session_id)

@app.post("/intake/sessions")
async def create_intake_session():
    """Create a new intake meeting session"""
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "websocket_url": f"/ws/intake/{session_id}",
        "status": "created"
    }

@app.get("/intake/sessions/{session_id}/summary")
async def get_intake_session_summary(session_id: str):
    """Get summary of an intake meeting session"""
    if session_id not in realtime_service.active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    meeting_state = realtime_service.active_sessions[session_id]
    
    return {
        "session_id": session_id,
        "participants": meeting_state.participants,
        "start_time": meeting_state.start_time.isoformat(),
        "duration_minutes": (datetime.now(timezone.utc) - meeting_state.start_time).total_seconds() / 60,
        "transcript_length": len(meeting_state.current_transcript),
        "requirements_count": len(meeting_state.requirements),
        "questions_generated": len(meeting_state.suggested_questions),
        "missing_info": list(meeting_state.missing_info)
    }

# ============================================================================
# CONTINUOUS LEARNING ENDPOINTS
# ============================================================================

class FeedbackSubmissionRequest(BaseModel):
    feedback_type: str
    source: str
    session_id: Optional[str] = None
    candidate_id: Optional[str] = None
    client_id: Optional[str] = None
    placement_id: Optional[str] = None
    score: float
    metadata: Dict[str, Any] = {}

class PlacementOutcomeRequest(BaseModel):
    placement_id: str
    candidate_id: str
    client_id: str
    success: bool
    satisfaction_score: Optional[float] = None
    duration_days: Optional[int] = None
    salary_achieved: Optional[float] = None
    feedback_notes: Optional[str] = None

@app.post("/learning/feedback")
async def submit_feedback(request: FeedbackSubmissionRequest):
    """Submit feedback for continuous learning."""
    try:
        feedback = FeedbackData(
            id=str(uuid.uuid4()),
            feedback_type=FeedbackType(request.feedback_type),
            source=FeedbackSource(request.source),
            session_id=request.session_id,
            candidate_id=request.candidate_id,
            client_id=request.client_id,
            placement_id=request.placement_id,
            score=request.score,
            metadata=request.metadata,
            timestamp=datetime.now(timezone.utc),
            processed=False
        )
        
        continuous_learning.add_feedback(feedback)
        
        return {
            "feedback_id": feedback.id,
            "status": "submitted",
            "message": "Feedback submitted for processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {e}")

@app.post("/learning/placement-outcome")
async def record_placement_outcome(request: PlacementOutcomeRequest):
    """Record placement outcome for learning."""
    try:
        # Create feedback for placement success
        placement_feedback = FeedbackData(
            id=str(uuid.uuid4()),
            feedback_type=FeedbackType.PLACEMENT_SUCCESS,
            source=FeedbackSource.PLACEMENT_OUTCOME,
            session_id=None,
            candidate_id=request.candidate_id,
            client_id=request.client_id,
            placement_id=request.placement_id,
            score=1.0 if request.success else 0.0,
            metadata={
                "satisfaction_score": request.satisfaction_score,
                "duration_days": request.duration_days,
                "salary_achieved": request.salary_achieved,
                "feedback_notes": request.feedback_notes
            },
            timestamp=datetime.now(timezone.utc),
            processed=False
        )
        
        continuous_learning.add_feedback(placement_feedback)
        
        # Also create client satisfaction feedback if score provided
        if request.satisfaction_score is not None:
            satisfaction_feedback = FeedbackData(
                id=str(uuid.uuid4()),
                feedback_type=FeedbackType.CLIENT_SATISFACTION,
                source=FeedbackSource.CLIENT_RESPONSE,
                session_id=None,
                candidate_id=request.candidate_id,
                client_id=request.client_id,
                placement_id=request.placement_id,
                score=request.satisfaction_score / 10.0,  # Normalize to 0-1
                metadata={
                    "placement_success": request.success,
                    "duration_days": request.duration_days,
                    "salary_achieved": request.salary_achieved
                },
                timestamp=datetime.now(timezone.utc),
                processed=False
            )
            
            continuous_learning.add_feedback(satisfaction_feedback)
        
        return {
            "placement_id": request.placement_id,
            "status": "recorded",
            "message": "Placement outcome recorded for learning"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record placement outcome: {e}")

@app.get("/learning/performance/{model_name}")
async def get_model_performance(model_name: str):
    """Get performance metrics for a specific model."""
    try:
        performance = continuous_learning.get_model_performance(model_name)
        
        if performance:
            return {
                "model_name": performance.model_name,
                "version": performance.version,
                "accuracy": performance.accuracy,
                "precision": performance.precision,
                "recall": performance.recall,
                "f1_score": performance.f1_score,
                "training_samples": performance.training_samples,
                "test_samples": performance.test_samples,
                "last_updated": performance.last_updated.isoformat(),
                "performance_trend": performance.performance_trend
            }
        else:
            return {
                "model_name": model_name,
                "message": "No performance data available"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model performance: {e}")

@app.get("/learning/signals")
async def get_learning_signals():
    """Get learning signals from recent feedback."""
    try:
        signals = continuous_learning.get_learning_signals()
        
        return {
            "signals": [
                {
                    "feature_name": signal.feature_name,
                    "importance_score": signal.importance_score,
                    "direction": signal.direction,
                    "confidence": signal.confidence,
                    "sample_size": signal.sample_size,
                    "timestamp": signal.timestamp.isoformat()
                }
                for signal in signals
            ],
            "total_signals": len(signals)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning signals: {e}")

@app.get("/learning/analytics")
async def get_learning_analytics(days: int = 30):
    """Get comprehensive learning analytics."""
    try:
        # Get feedback statistics
        session = get_session()
        
        # Recent feedback count by type
        feedback_stats = session.execute(text("""
            SELECT 
                feedback_type,
                COUNT(*) as count,
                AVG(score) as avg_score
            FROM feedback_data 
            WHERE timestamp >= :start_date
            GROUP BY feedback_type
        """), {
            "start_date": datetime.now(timezone.utc) - timedelta(days=days)
        }).fetchall()
        
        # Model performance trends
        performance_trends = session.execute(text("""
            SELECT 
                model_name,
                AVG(accuracy) as avg_accuracy,
                AVG(f1_score) as avg_f1,
                COUNT(*) as evaluations
            FROM model_performance 
            WHERE last_updated >= :start_date
            GROUP BY model_name
        """), {
            "start_date": datetime.now(timezone.utc) - timedelta(days=days)
        }).fetchall()
        
        # Placement success rate
        placement_stats = session.execute(text("""
            SELECT 
                COUNT(*) as total_placements,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_placements,
                AVG(satisfaction_score) as avg_satisfaction
            FROM placement_outcomes 
            WHERE outcome_date >= :start_date
        """), {
            "start_date": datetime.now(timezone.utc) - timedelta(days=days)
        }).fetchone()
        
        session.close()
        
        return {
            "period_days": days,
            "feedback_statistics": [
                {
                    "type": row.feedback_type,
                    "count": row.count,
                    "average_score": float(row.avg_score) if row.avg_score else 0.0
                }
                for row in feedback_stats
            ],
            "model_performance": [
                {
                    "model_name": row.model_name,
                    "average_accuracy": float(row.avg_accuracy) if row.avg_accuracy else 0.0,
                    "average_f1": float(row.avg_f1) if row.avg_f1 else 0.0,
                    "evaluations": row.evaluations
                }
                for row in performance_trends
            ],
            "placement_analytics": {
                "total_placements": placement_stats.total_placements or 0,
                "successful_placements": placement_stats.successful_placements or 0,
                "success_rate": (placement_stats.successful_placements / placement_stats.total_placements * 100) if placement_stats.total_placements else 0,
                "average_satisfaction": float(placement_stats.avg_satisfaction) if placement_stats.avg_satisfaction else 0.0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning analytics: {e}")

@app.post("/learning/trigger-retraining/{model_name}")
async def trigger_model_retraining(model_name: str):
    """Manually trigger model retraining."""
    try:
        # This would trigger a full retraining pipeline
        logger.info(f"Manual retraining triggered for model: {model_name}")
        
        return {
            "model_name": model_name,
            "status": "retraining_triggered",
            "message": f"Retraining pipeline started for {model_name}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger retraining: {e}")

# Include router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 