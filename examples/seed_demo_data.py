#!/usr/bin/env python3
"""
Seed the Robot Recruiter database with demo data (users, candidates, feedback, assignments).
Uses SQLite by default for fast local development/demo.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.github_talent_intelligence.db import Base, User, Feedback, ReviewSession, ReviewAssignment

# Use SQLite by default, but allow override
DB_URL = os.environ.get("ROBOT_RECRUITER_DB_URL", "sqlite:///robot_recruiter_demo.db")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Drop all tables if using SQLite (for a fresh start)
if DB_URL.startswith("sqlite"):
    Base.metadata.drop_all(bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# --- USERS ---
recruiter = User(
    name="Alice Recruiter",
    email="alice@company.com",
    role="recruiter",
    is_active=True
)
reviewer = User(
    name="Bob Reviewer",
    email="bob@company.com",
    role="reviewer",
    reviewer_level="senior",
    is_active=True
)
session.add_all([recruiter, reviewer])
session.commit()
session.refresh(recruiter)
session.refresh(reviewer)

# --- CANDIDATES (as Feedback for demo) ---
candidate1 = Feedback(
    repo_full_name="octocat/Hello-World",
    suggested_category="Backend",
    reason="Strong Python skills, active contributor",
    user_id=recruiter.id,
    status="pending"
)
candidate2 = Feedback(
    repo_full_name="torvalds/linux",
    suggested_category="Systems",
    reason="Kernel contributions, C expertise",
    user_id=recruiter.id,
    status="pending"
)
session.add_all([candidate1, candidate2])
session.commit()
session.refresh(candidate1)
session.refresh(candidate2)

# --- REVIEW SESSION ---
review_session = ReviewSession(
    name="Demo Review Session",
    description="Demo session for MVP",
    reviewer_id=reviewer.id,
    status="active",
    created_at=datetime.now(),
    target_completion_date=datetime.now() + timedelta(days=7)
)
session.add(review_session)
session.commit()
session.refresh(review_session)

# --- ASSIGN FEEDBACK TO REVIEWER ---
assignment1 = ReviewAssignment(
    feedback_id=candidate1.id,
    reviewer_id=reviewer.id,
    review_session_id=review_session.id,
    assigned_at=datetime.now(),
    due_date=datetime.now() + timedelta(days=3),
    priority="high",
    status="assigned"
)
assignment2 = ReviewAssignment(
    feedback_id=candidate2.id,
    reviewer_id=reviewer.id,
    review_session_id=review_session.id,
    assigned_at=datetime.now(),
    due_date=datetime.now() + timedelta(days=3),
    priority="normal",
    status="assigned"
)
session.add_all([assignment1, assignment2])
session.commit()

print("✅ Demo data seeded!")
print(f"Users: {session.query(User).count()}")
print(f"Feedback/Candidates: {session.query(Feedback).count()}")
print(f"Review Sessions: {session.query(ReviewSession).count()}")
print(f"Assignments: {session.query(ReviewAssignment).count()}")

session.close() 