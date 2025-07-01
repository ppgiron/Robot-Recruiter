import os
import pytest
from fastapi.testclient import TestClient
from src.github_talent_intelligence.api import app
from src.github_talent_intelligence.db import (
    ChatGPTInteraction,
    Feedback,
    User,
    get_session,
    init_db,
)
from src.github_talent_intelligence.gpt_stub import get_chatgpt_suggestion
import uuid

TEST_DB_PATH = "sqlite:///test.db"

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database and clean up after each test."""
    # Use a unique test database
    os.environ["ROBOT_RECRUITER_DB_URL"] = "sqlite:///test_feedback.db"
    init_db()
    yield
    # Clean up
    if os.path.exists("test_feedback.db"):
        os.remove("test_feedback.db")


def test_add_user_and_feedback():
    db = get_session()
    user = User(name="Test User", email="test@example.com", role="reviewer")
    db.add(user)
    db.commit()
    feedback = Feedback(
        repo_full_name="octocat/Hello-World",
        suggested_category="Backend",
        reason="API project",
        user_id=user.id,
    )
    db.add(feedback)
    db.commit()
    # Retrieve and check
    fb = db.query(Feedback).first()
    assert fb.repo_full_name == "octocat/Hello-World"
    assert fb.suggested_category == "Backend"
    assert fb.user_id == user.id
    db.close()


def test_chatgpt_stub_saves_interaction():
    db = get_session()
    prompt = "Suggest a category for a repo about React."
    response = get_chatgpt_suggestion(prompt)
    interaction = db.query(ChatGPTInteraction).filter_by(prompt=prompt).first()
    assert interaction is not None
    assert interaction.response == response
    db.close()


def setup_feedback():
    db = get_session()
    # Use unique email to avoid constraint violations
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    user = User(name="Test User", email=unique_email, role="recruiter")
    db.add(user)
    db.commit()
    feedback = Feedback(repo_full_name="test/repo", suggested_category="Backend", reason="Test reason", user_id=user.id)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    db.close()
    return feedback.id


def test_generate_chatgpt_suggestion_default_temp(monkeypatch):
    feedback_id = setup_feedback()
    def mock_get_chatgpt_suggestion(prompt, feedback_id=None, model="gpt-3.5-turbo", temperature=0.2, version=1):
        return f"[MOCKED] Suggestion for feedback {feedback_id} at temp {temperature}"
    # Mock at the correct import path used in the API
    monkeypatch.setattr("src.github_talent_intelligence.api.get_chatgpt_suggestion", mock_get_chatgpt_suggestion)
    response = client.post("/chatgpt/suggestion", json={"feedback_id": feedback_id})
    assert response.status_code == 200
    assert "[MOCKED] Suggestion" in response.json()["suggestion"]


def test_generate_chatgpt_suggestion_custom_temp(monkeypatch):
    feedback_id = setup_feedback()
    def mock_get_chatgpt_suggestion(prompt, feedback_id=None, model="gpt-3.5-turbo", temperature=0.2, version=1):
        return f"[MOCKED] Suggestion for feedback {feedback_id} at temp {temperature}"
    # Mock at the correct import path used in the API
    monkeypatch.setattr("src.github_talent_intelligence.api.get_chatgpt_suggestion", mock_get_chatgpt_suggestion)
    response = client.post("/chatgpt/suggestion", json={"feedback_id": feedback_id, "temperature": 0.7})
    assert response.status_code == 200
    assert "at temp 0.7" in response.json()["suggestion"]
