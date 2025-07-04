"""Example tests demonstrating hybrid SQLite/PostgreSQL approach."""

import pytest
from sqlalchemy.orm import Session
import uuid

from src.github_talent_intelligence.db import User, Feedback, ChatGPTInteraction
from src.github_talent_intelligence.candidate_db import Repository, Contributor, CandidateProfile


class TestUnitTests:
    """Unit tests using SQLite (fast)."""
    
    @pytest.mark.unit
    @pytest.mark.sqlite
    def test_user_creation_sqlite(self, sqlite_session: Session):
        """Test user creation with SQLite."""
        user = User(name="Test User", email="test@example.com", role="recruiter")
        sqlite_session.add(user)
        sqlite_session.commit()
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
    
    @pytest.mark.unit
    @pytest.mark.sqlite
    def test_feedback_creation_sqlite(self, sqlite_session: Session):
        """Test feedback creation with SQLite."""
        # Create user first with unique email
        unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        user = User(name="Test User", email=unique_email, role="recruiter")
        sqlite_session.add(user)
        sqlite_session.commit()
        
        # Create feedback
        feedback = Feedback(
            repo_full_name="test/repo",
            suggested_category="Backend",
            reason="Test reason",
            user_id=user.id
        )
        sqlite_session.add(feedback)
        sqlite_session.commit()
        
        assert feedback.id is not None
        assert feedback.repo_full_name == "test/repo"
        assert feedback.suggested_category == "Backend"
    
    @pytest.mark.unit
    @pytest.mark.sqlite
    def test_candidate_profile_sqlite(self, sqlite_db_manager):
        """Test candidate profile operations with SQLite."""
        # Create candidate profile
        session = sqlite_db_manager.get_session()
        try:
            candidate = CandidateProfile(
                github_id=12345,
                login='testuser',
                name='Test User',
                company='Test Company',
                location='Test City',
                total_contributions=100,
                repositories_contributed=5,
                followers=200
            )
            session.add(candidate)
            session.commit()
            
            # Retrieve candidate
            found_candidate = sqlite_db_manager.get_candidate_by_github_id(12345)
            assert found_candidate is not None
            assert found_candidate.login == 'testuser'
            assert found_candidate.company == 'Test Company'
            
        finally:
            session.close()


class TestIntegrationTests:
    """Integration tests using PostgreSQL (production-like)."""
    
    @pytest.mark.integration
    @pytest.mark.postgresql
    def test_user_creation_postgresql(self, postgresql_session: Session):
        """Test user creation with PostgreSQL."""
        user = User(name="Test User", email="test@example.com", role="recruiter")
        postgresql_session.add(user)
        postgresql_session.commit()
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
    
    @pytest.mark.integration
    @pytest.mark.postgresql
    def test_feedback_creation_postgresql(self, postgresql_session: Session):
        """Test feedback creation with PostgreSQL."""
        # Create user first
        user = User(name="Test User", email="test@example.com", role="recruiter")
        postgresql_session.add(user)
        postgresql_session.commit()
        
        # Create feedback
        feedback = Feedback(
            repo_full_name="test/repo",
            suggested_category="Backend",
            reason="Test reason",
            user_id=user.id
        )
        postgresql_session.add(feedback)
        postgresql_session.commit()
        
        assert feedback.id is not None
        assert feedback.repo_full_name == "test/repo"
        assert feedback.suggested_category == "Backend"
    
    @pytest.mark.integration
    @pytest.mark.postgresql
    def test_candidate_profile_postgresql(self, postgresql_db_manager):
        """Test candidate profile operations with PostgreSQL."""
        # Create candidate profile
        session = postgresql_db_manager.get_session()
        try:
            candidate = CandidateProfile(
                github_id=12345,
                login='testuser',
                name='Test User',
                company='Test Company',
                location='Test City',
                total_contributions=100,
                repositories_contributed=5,
                followers=200
            )
            session.add(candidate)
            session.commit()
            
            # Retrieve candidate
            found_candidate = postgresql_db_manager.get_candidate_by_github_id(12345)
            assert found_candidate is not None
            assert found_candidate.login == 'testuser'
            assert found_candidate.company == 'Test Company'
            
        finally:
            session.close()
    
    @pytest.mark.integration
    @pytest.mark.postgresql
    def test_postgresql_specific_features(self, postgresql_session: Session):
        """Test PostgreSQL-specific features like UUID and JSON."""
        # Test UUID generation (PostgreSQL specific)
        user = User(name="Test User", email="test@example.com", role="recruiter")
        postgresql_session.add(user)
        postgresql_session.commit()
        
        # Verify UUID is generated
        assert user.id is not None
        assert str(user.id).count('-') == 4  # UUID format
        
        # Test JSON field (if applicable)
        # This would test any JSON fields in your models


class TestCrossDatabaseTests:
    """Tests that compare behavior between SQLite and PostgreSQL."""
    
    @pytest.mark.integration
    def test_data_consistency(self, sqlite_session: Session, postgresql_session: Session):
        """Test that data is consistent between SQLite and PostgreSQL."""
        # Create same data in both databases
        sqlite_user = User(name="Test User", email="test@example.com", role="recruiter")
        postgresql_user = User(name="Test User", email="test@example.com", role="recruiter")
        
        sqlite_session.add(sqlite_user)
        postgresql_session.add(postgresql_user)
        
        sqlite_session.commit()
        postgresql_session.commit()
        
        # Verify both have IDs (though they might be different types)
        assert sqlite_user.id is not None
        assert postgresql_user.id is not None
        
        # Verify other fields are identical
        assert sqlite_user.name == postgresql_user.name
        assert sqlite_user.email == postgresql_user.email
        assert sqlite_user.role == postgresql_user.role 