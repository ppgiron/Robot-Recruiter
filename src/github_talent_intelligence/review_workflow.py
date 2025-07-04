"""
Review Workflow Management
Handles reviewer assignments, status transitions, and review sessions.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .db import (
    get_session, User, Feedback, ReviewSession, ReviewAssignment,
    VoiceNote, Transcription, VoiceEnhancedSuggestion
)


class ReviewWorkflowManager:
    """Manages the review workflow and assignments."""
    
    def __init__(self):
        self.db = get_session()
    
    def __del__(self):
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
    def create_review_session(self, 
                            name: str, 
                            reviewer_id: int, 
                            description: Optional[str] = None,
                            target_completion_date: Optional[datetime] = None) -> ReviewSession:
        """Create a new review session."""
        session = ReviewSession(
            name=name,
            description=description,
            reviewer_id=reviewer_id,
            target_completion_date=target_completion_date
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def assign_feedback_to_reviewer(self, 
                                  feedback_id: int, 
                                  reviewer_id: int,
                                  review_session_id: Optional[int] = None,
                                  priority: str = "normal",
                                  due_date: Optional[datetime] = None,
                                  notes: Optional[str] = None) -> ReviewAssignment:
        """Assign a feedback item to a reviewer."""
        # Check if reviewer exists and is active
        reviewer = self.db.query(User).filter(
            and_(User.id == reviewer_id, User.is_active == True)
        ).first()
        if not reviewer:
            raise ValueError(f"Reviewer with ID {reviewer_id} not found or inactive")
        
        # Check if feedback exists
        feedback = self.db.query(Feedback).get(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback with ID {feedback_id} not found")
        
        # Create assignment
        assignment = ReviewAssignment(
            feedback_id=feedback_id,
            reviewer_id=reviewer_id,
            review_session_id=review_session_id,
            priority=priority,
            due_date=due_date,
            notes=notes
        )
        
        # Update feedback status
        feedback.status = "assigned"
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def get_reviewer_assignments(self, 
                               reviewer_id: int, 
                               status: Optional[str] = None,
                               include_overdue: bool = True) -> List[Dict[str, Any]]:
        """Get all assignments for a reviewer."""
        query = self.db.query(ReviewAssignment).filter(ReviewAssignment.reviewer_id == reviewer_id)
        
        if status:
            query = query.filter(ReviewAssignment.status == status)
        
        assignments = query.all()
        
        results = []
        for assignment in assignments:
            # Check if overdue
            is_overdue = False
            if assignment.due_date and assignment.due_date < datetime.now():
                is_overdue = True
                if include_overdue and assignment.status != "completed":
                    assignment.status = "overdue"
                    self.db.commit()
            
            # Get feedback details
            feedback = assignment.feedback
            voice_notes_count = len(feedback.voice_notes) if feedback.voice_notes else 0
            
            results.append({
                "assignment_id": assignment.id,
                "feedback_id": assignment.feedback_id,
                "repo_full_name": feedback.repo_full_name,
                "suggested_category": feedback.suggested_category,
                "priority": assignment.priority,
                "status": assignment.status,
                "assigned_at": assignment.assigned_at.isoformat(),
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "is_overdue": is_overdue,
                "voice_notes_count": voice_notes_count,
                "notes": assignment.notes
            })
        
        return results
    
    def update_assignment_status(self, 
                               assignment_id: int, 
                               status: str,
                               notes: Optional[str] = None) -> ReviewAssignment:
        """Update the status of a review assignment."""
        assignment = self.db.query(ReviewAssignment).get(assignment_id)
        if not assignment:
            raise ValueError(f"Assignment with ID {assignment_id} not found")
        
        assignment.status = status
        if notes:
            assignment.notes = notes
        
        # Update feedback status accordingly
        feedback = assignment.feedback
        if status == "in_review":
            feedback.status = "in_review"
        elif status == "completed":
            feedback.status = "pending"  # Ready for final review
        
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
    
    def submit_review(self, 
                     feedback_id: int, 
                     reviewer_id: int,
                     review_decision: str,  # approved, rejected, needs_revision
                     review_notes: Optional[str] = None,
                     voice_note_id: Optional[int] = None) -> Feedback:
        """Submit a review decision for a feedback item."""
        feedback = self.db.query(Feedback).get(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback with ID {feedback_id} not found")
        
        # Validate reviewer has assignment
        assignment = self.db.query(ReviewAssignment).filter(
            and_(
                ReviewAssignment.feedback_id == feedback_id,
                ReviewAssignment.reviewer_id == reviewer_id
            )
        ).first()
        
        if not assignment:
            raise ValueError(f"Reviewer {reviewer_id} is not assigned to feedback {feedback_id}")
        
        # Update feedback
        feedback.status = review_decision
        feedback.review_notes = review_notes
        feedback.reviewed_at = datetime.now()
        feedback.reviewed_by = reviewer_id
        
        # Update assignment
        assignment.status = "completed"
        
        # If voice note provided, link it
        if voice_note_id:
            voice_note = self.db.query(VoiceNote).get(voice_note_id)
            if voice_note:
                voice_note.feedback_id = feedback_id
        
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    def get_review_session_summary(self, session_id: int) -> Dict[str, Any]:
        """Get summary statistics for a review session."""
        session = self.db.query(ReviewSession).get(session_id)
        if not session:
            raise ValueError(f"Review session with ID {session_id} not found")
        
        # Get assignments for this session
        assignments = self.db.query(ReviewAssignment).filter(
            ReviewAssignment.review_session_id == session_id
        ).all()
        
        # Calculate statistics
        total_assignments = len(assignments)
        completed = len([a for a in assignments if a.status == "completed"])
        in_review = len([a for a in assignments if a.status == "in_review"])
        overdue = len([a for a in assignments if a.due_date and a.due_date < datetime.now() and a.status != "completed"])
        
        # Get feedback status breakdown
        feedback_statuses = {}
        for assignment in assignments:
            status = assignment.feedback.status
            feedback_statuses[status] = feedback_statuses.get(status, 0) + 1
        
        return {
            "session_id": session.id,
            "session_name": session.name,
            "reviewer_id": session.reviewer_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "target_completion_date": session.target_completion_date.isoformat() if session.target_completion_date else None,
            "statistics": {
                "total_assignments": total_assignments,
                "completed": completed,
                "in_review": in_review,
                "overdue": overdue,
                "completion_rate": (completed / total_assignments * 100) if total_assignments > 0 else 0
            },
            "feedback_statuses": feedback_statuses
        }
    
    def auto_assign_pending_feedback(self, 
                                   reviewer_id: int,
                                   max_assignments: int = 10,
                                   priority_filter: Optional[str] = None) -> List[ReviewAssignment]:
        """Automatically assign pending feedback to a reviewer."""
        # Get pending feedback not yet assigned
        query = self.db.query(Feedback).filter(
            and_(
                Feedback.status == "pending",
                ~Feedback.id.in_(
                    self.db.query(ReviewAssignment.feedback_id)
                )
            )
        )
        
        if priority_filter:
            # This would need to be implemented based on your priority logic
            pass
        
        pending_feedback = query.limit(max_assignments).all()
        
        assignments = []
        for feedback in pending_feedback:
            assignment = self.assign_feedback_to_reviewer(
                feedback_id=feedback.id,
                reviewer_id=reviewer_id
            )
            assignments.append(assignment)
        
        return assignments
    
    def get_reviewer_performance_stats(self, reviewer_id: int, days: int = 30) -> Dict[str, Any]:
        """Get performance statistics for a reviewer."""
        since_date = datetime.now() - timedelta(days=days)
        
        # Get completed assignments
        completed_assignments = self.db.query(ReviewAssignment).filter(
            and_(
                ReviewAssignment.reviewer_id == reviewer_id,
                ReviewAssignment.status == "completed",
                ReviewAssignment.assigned_at >= since_date
            )
        ).all()
        
        # Get feedback decisions
        feedback_decisions = self.db.query(Feedback).filter(
            and_(
                Feedback.reviewed_by == reviewer_id,
                Feedback.reviewed_at >= since_date
            )
        ).all()
        
        # Calculate statistics
        total_completed = len(completed_assignments)
        avg_completion_time = 0
        if total_completed > 0:
            total_time = sum([
                (a.feedback.reviewed_at - a.assigned_at).total_seconds() 
                for a in completed_assignments 
                if a.feedback.reviewed_at
            ])
            avg_completion_time = total_time / total_completed / 3600  # hours
        
        decision_breakdown = {}
        for feedback in feedback_decisions:
            decision = feedback.status
            decision_breakdown[decision] = decision_breakdown.get(decision, 0) + 1
        
        return {
            "reviewer_id": reviewer_id,
            "period_days": days,
            "total_completed": total_completed,
            "avg_completion_time_hours": round(avg_completion_time, 2),
            "decision_breakdown": decision_breakdown,
            "completion_rate": "N/A"  # Would need total assigned for this period
        } 