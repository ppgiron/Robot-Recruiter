import os

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
    Float,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


def get_engine():
    db_url = os.getenv(
        "ROBOT_RECRUITER_DB_URL",
        "postgresql://postgres:postgres@localhost:5432/robot_recruiter",
    )
    return create_engine(db_url)


def get_session():
    engine = get_engine()
    return sessionmaker(bind=engine)()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    role = Column(String(50), nullable=False)  # e.g. recruiter, reviewer, admin
    feedback = relationship("Feedback", back_populates="user")
    review_sessions = relationship("ReviewSession", back_populates="user")


class ReviewSession(Base):
    __tablename__ = "review_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="open")
    user = relationship("User", back_populates="review_sessions")
    feedback = relationship("Feedback", back_populates="review_session")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    repo_full_name = Column(String(200), nullable=False)
    suggested_category = Column(String(100), nullable=False)
    reason = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    review_session_id = Column(Integer, ForeignKey("review_sessions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="pending")
    user = relationship("User", back_populates="feedback")
    review_session = relationship("ReviewSession", back_populates="feedback")


class ChatGPTInteraction(Base):
    __tablename__ = "chatgpt_interactions"
    id = Column(Integer, primary_key=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    model = Column(String(100), default="gpt-3.5-turbo")
    temperature = Column(Integer, default=2)  # Store as int*10 (e.g., 2 for 0.2)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_status = Column(String(50), default="pending")  # pending, approved, rejected
    review_comment = Column(Text, nullable=True)
    feedback = relationship("Feedback", backref="chatgpt_interactions")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class VoiceNote(Base):
    """Voice notes for feedback and reviews."""
    __tablename__ = "voice_notes"
    id = Column(Integer, primary_key=True)
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audio_file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer)
    duration_seconds = Column(Float)
    audio_format = Column(String(20))  # wav, mp3, m4a, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    storage_type = Column(String(20), default="local")  # local, cloud
    cloud_url = Column(String(500), nullable=True)
    
    # Relationships
    feedback = relationship("Feedback", backref="voice_notes")
    user = relationship("User", backref="voice_notes")
    transcription = relationship("Transcription", back_populates="voice_note", uselist=False)
    enhanced_suggestions = relationship("VoiceEnhancedSuggestion", back_populates="voice_note")


class Transcription(Base):
    """Transcriptions of voice notes using Whisper."""
    __tablename__ = "transcriptions"
    id = Column(Integer, primary_key=True)
    voice_note_id = Column(Integer, ForeignKey("voice_notes.id"), nullable=False)
    text = Column(Text, nullable=False)
    confidence_score = Column(Float)
    language = Column(String(10))
    whisper_model = Column(String(20), default="base")  # tiny, base, small, etc.
    processing_time_seconds = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    voice_note = relationship("VoiceNote", back_populates="transcription")


class VoiceEnhancedSuggestion(Base):
    """Enhanced suggestions based on voice note transcriptions."""
    __tablename__ = "voice_enhanced_suggestions"
    id = Column(Integer, primary_key=True)
    voice_note_id = Column(Integer, ForeignKey("voice_notes.id"), nullable=False)
    original_suggestion_id = Column(Integer, ForeignKey("chatgpt_interactions.id"), nullable=True)
    voice_context = Column(Text, nullable=False)  # Combined transcription + feedback context
    enhanced_suggestion = Column(Text, nullable=False)
    ai_analysis = Column(Text)  # Additional AI insights
    model = Column(String(100), default="gpt-3.5-turbo")
    temperature = Column(Integer, default=2)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    voice_note = relationship("VoiceNote", back_populates="enhanced_suggestions")
    original_suggestion = relationship("ChatGPTInteraction", foreign_keys=[original_suggestion_id])


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
