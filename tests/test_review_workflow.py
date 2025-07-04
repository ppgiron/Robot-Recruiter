"""
Tests for review workflow functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

from src.github_talent_intelligence.review_workflow import ReviewWorkflowManager
from src.github_talent_intelligence.db import get_session, User, Feedback, ReviewSession, ReviewAssignment, Base
from tests.conftest import TestBase


class TestReviewWorkflowManager(TestBase):
    """Test review workflow management functionality."""
    
    @pytest.fixture
    def setup_test_data(self, request):
        db = self.session
        reviewer = User(
            name="Test Reviewer",
            email="reviewer@test.com",
            role="reviewer",
            reviewer_level="senior",
            is_active=True
        )
        db.add(reviewer)
        user = User(
            name="Test User",
            email="user@test.com",
            role="recruiter",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(reviewer)
        db.refresh(user)
        feedback = Feedback(
            repo_full_name="test/repo",
            suggested_category="Backend",
            reason="Test feedback",
            user_id=user.id,
            status="pending"
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return {
            "reviewer_id": reviewer.id,
            "user_id": user.id,
            "feedback_id": feedback.id,
            "reviewer_email": reviewer.email,
            "user_email": user.email
        }
    
    def test_create_review_session(self, setup_test_data):
        manager = ReviewWorkflowManager()
        session = manager.create_review_session(
            name="Test Session",
            reviewer_id=setup_test_data["reviewer_id"],
            description="Test description",
            target_completion_date=datetime.now() + timedelta(days=7)
        )
        assert session.name == "Test Session"
        assert session.reviewer_id == setup_test_data["reviewer_id"]
        assert session.description == "Test description"
    
    def test_assign_feedback_to_reviewer(self, setup_test_data):
        manager = ReviewWorkflowManager()
        assignment = manager.assign_feedback_to_reviewer(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"],
            priority="high",
            due_date=datetime.now() + timedelta(days=3)
        )
        assert assignment.feedback_id == setup_test_data["feedback_id"]
        assert assignment.reviewer_id == setup_test_data["reviewer_id"]
        assert assignment.priority == "high"
    
    def test_assign_feedback_invalid_reviewer(self, setup_test_data):
        manager = ReviewWorkflowManager()
        with pytest.raises(ValueError, match="Reviewer with ID"):
            manager.assign_feedback_to_reviewer(
                feedback_id=setup_test_data["feedback_id"],
                reviewer_id=uuid.uuid4()  # Invalid reviewer ID
            )
    
    def test_get_reviewer_assignments(self, setup_test_data):
        manager = ReviewWorkflowManager()
        # First, assign feedback
        manager.assign_feedback_to_reviewer(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"]
        )
        assignments = manager.get_reviewer_assignments(
            reviewer_id=setup_test_data["reviewer_id"]
        )
        assert len(assignments) == 1
        assignment = assignments[0]
        assert assignment["feedback_id"] == setup_test_data["feedback_id"]
        assert assignment["priority"] == "normal"
        assert assignment["status"] == "assigned"
    
    def test_update_assignment_status(self, setup_test_data):
        manager = ReviewWorkflowManager()
        # Assign feedback first
        assignment = manager.assign_feedback_to_reviewer(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"]
        )
        updated = manager.update_assignment_status(
            assignment_id=assignment.id,
            status="in_review",
            notes="Started review"
        )
        assert updated.status == "in_review"
        assert updated.notes == "Started review"
    
    def test_submit_review(self, setup_test_data):
        manager = ReviewWorkflowManager()
        # Assign feedback first
        manager.assign_feedback_to_reviewer(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"]
        )
        feedback = manager.submit_review(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"],
            review_decision="approved",
            review_notes="Great candidate!"
        )
        assert feedback.status == "approved"
        assert feedback.review_notes == "Great candidate!"
        assert feedback.reviewed_by == setup_test_data["reviewer_id"]
        assert feedback.reviewed_at is not None
    
    def test_submit_review_no_assignment(self, setup_test_data):
        manager = ReviewWorkflowManager()
        # Mock feedback
        mock_feedback = Mock()
        mock_feedback.id = setup_test_data["feedback_id"]
        
        # Mock assignment query to return None (no assignment)
        mock_session = Mock()
        mock_session.query.return_value.get.return_value = mock_feedback
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Reviewer.*is not assigned"):
            manager.submit_review(
                feedback_id=setup_test_data["feedback_id"],
                reviewer_id=setup_test_data["reviewer_id"],
                review_decision="approved"
            )
    
    def test_get_review_session_summary(self, setup_test_data):
        manager = ReviewWorkflowManager()
        # Create review session
        session = manager.create_review_session(
            name="Test Session",
            reviewer_id=setup_test_data["reviewer_id"],
            description="Test description",
            target_completion_date=datetime.now() + timedelta(days=7)
        )
        # Assign feedback to this session
        manager.assign_feedback_to_reviewer(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"],
            review_session_id=session.id
        )
        summary = manager.get_review_session_summary(session.id)
        assert summary["session_id"] == session.id
        assert summary["session_name"] == "Test Session"
        assert summary["reviewer_id"] == setup_test_data["reviewer_id"]
        assert summary["statistics"]["total_assignments"] == 1
    
    def test_auto_assign_pending_feedback(self, setup_test_data):
        manager = ReviewWorkflowManager()
        # Mock pending feedback
        mock_feedback = Mock()
        mock_feedback.id = setup_test_data["feedback_id"]
        mock_feedback.repo_full_name = "test/repo"
        
        # Mock assignment query to return empty (no existing assignments)
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value.get.return_value = mock_feedback
        
        # Mock the assign_feedback_to_reviewer method
        with patch.object(manager, 'assign_feedback_to_reviewer') as mock_assign:
            mock_assignment = Mock()
            mock_assign.return_value = mock_assignment
            
            assignments = manager.auto_assign_pending_feedback(
                reviewer_id=setup_test_data["reviewer_id"],
                max_assignments=5
            )
            
            assert len(assignments) == 1
            mock_assign.assert_called_once_with(
                feedback_id=setup_test_data["feedback_id"],
                reviewer_id=setup_test_data["reviewer_id"]
            )
    
    def test_get_reviewer_performance_stats(self, setup_test_data):
        manager = ReviewWorkflowManager()
        # Assign feedback and submit review
        manager.assign_feedback_to_reviewer(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"]
        )
        manager.submit_review(
            feedback_id=setup_test_data["feedback_id"],
            reviewer_id=setup_test_data["reviewer_id"],
            review_decision="approved"
        )
        stats = manager.get_reviewer_performance_stats(
            reviewer_id=setup_test_data["reviewer_id"],
            days=30
        )
        assert stats["reviewer_id"] == setup_test_data["reviewer_id"]
        assert stats["period_days"] == 30
        assert stats["total_completed"] == 1
        assert stats["decision_breakdown"]["approved"] == 1


class TestReviewWorkflowAPI:
    """Test review workflow API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from src.github_talent_intelligence.api import app
        return TestClient(app)
    
    def test_create_review_session_api(self, client):
        """Test creating review session via API."""
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock()
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "reviewer@test.com"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Mock workflow manager
        with patch('src.github_talent_intelligence.api.workflow_manager') as mock_workflow:
            mock_session_obj = Mock()
            mock_session_obj.id = 1
            mock_session_obj.name = "Test Session"
            mock_session_obj.reviewer_id = 1
            mock_session_obj.status = "active"
            mock_session_obj.created_at = datetime.now()
            mock_session_obj.target_completion_date = None
            
            mock_workflow.create_review_session.return_value = mock_session_obj
            
            response = client.post("/review-sessions", json={
                "name": "Test Session",
                "reviewer_email": "reviewer@test.com",
                "description": "Test description",
                "target_days": 7
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == 1
            assert data["name"] == "Test Session"
    
    def test_assign_feedback_api(self, client):
        """Test assigning feedback via API."""
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock()
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "reviewer@test.com"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Mock workflow manager
        with patch('src.github_talent_intelligence.api.workflow_manager') as mock_workflow:
            mock_assignment = Mock()
            mock_assignment.id = 1
            mock_assignment.feedback_id = 123
            mock_assignment.reviewer_id = 1
            mock_assignment.priority = "high"
            mock_assignment.status = "assigned"
            mock_assignment.assigned_at = datetime.now()
            mock_assignment.due_date = datetime.now() + timedelta(days=3)
            
            mock_workflow.assign_feedback_to_reviewer.return_value = mock_assignment
            
            response = client.post("/assignments", json={
                "feedback_id": 123,
                "reviewer_email": "reviewer@test.com",
                "priority": "high",
                "due_days": 3
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["assignment_id"] == 1
            assert data["feedback_id"] == 123
            assert data["priority"] == "high"
    
    def test_submit_review_api(self, client):
        """Test submitting review via API."""
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = Mock()
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "reviewer@test.com"
        
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Mock workflow manager
        with patch('src.github_talent_intelligence.api.workflow_manager') as mock_workflow:
            mock_feedback = Mock()
            mock_feedback.id = 123
            mock_feedback.status = "approved"
            mock_feedback.review_notes = "Great candidate!"
            mock_feedback.reviewed_at = datetime.now()
            mock_feedback.reviewed_by = 1
            
            mock_workflow.submit_review.return_value = mock_feedback
            
            response = client.post("/reviews/submit", json={
                "feedback_id": 123,
                "reviewer_email": "reviewer@test.com",
                "decision": "approved",
                "notes": "Great candidate!"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["feedback_id"] == 123
            assert data["status"] == "approved"
            assert data["review_notes"] == "Great candidate!" 