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


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
