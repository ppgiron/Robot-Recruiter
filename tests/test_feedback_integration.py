import os

import pytest

from src.github_talent_intelligence.db import (
    ChatGPTInteraction,
    Feedback,
    User,
    get_session,
    init_db,
)
from src.github_talent_intelligence.gpt_stub import get_chatgpt_suggestion

TEST_DB_PATH = "sqlite:///test.db"


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    os.environ["ROBOT_RECRUITER_DB_URL"] = TEST_DB_PATH
    init_db()
    yield
    # Clean up test DB file
    if os.path.exists("test.db"):
        os.remove("test.db")


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
