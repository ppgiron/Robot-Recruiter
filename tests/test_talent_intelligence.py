"""Test file for GitHub Talent Intelligence Platform."""

# Add your tests here

import os
import types

import pytest

from src.github_talent_intelligence.config_loader import load_categories
from src.github_talent_intelligence.talent_intelligence import TalentAnalyzer


@pytest.fixture
def analyzer():
    # Use a dummy token to avoid real API calls
    os.environ["GITHUB_TOKEN"] = "dummy_token"
    return TalentAnalyzer(github_token="dummy_token")


def test_load_categories():
    categories = load_categories()
    assert "Frontend" in categories
    assert "Backend" in categories
    assert isinstance(categories["Frontend"]["keywords"], list)


def test_classify_repo_weighted_frontend(analyzer):
    repo = {
        "name": "react-ui-library",
        "description": "A modern React component library for web UIs",
        "language": "JavaScript",
        "topics": ["react", "ui", "frontend"],
    }
    category = analyzer._classify_repo_weighted(repo)
    assert category == "Frontend"


def test_classify_repo_weighted_backend(analyzer):
    repo = {
        "name": "fastapi-backend",
        "description": "A FastAPI backend for scalable APIs",
        "language": "Python",
        "topics": ["api", "backend", "fastapi"],
    }
    category = analyzer._classify_repo_weighted(repo)
    assert category == "Backend"


def test_classify_repo_weighted_unclassified(analyzer):
    repo = {
        "name": "unknown-project",
        "description": "A project with no clear category",
        "language": "Esperanto",
        "topics": [],
    }
    category = analyzer._classify_repo_weighted(repo)
    assert category == "Unclassified"


def test_get_contributor_insights(monkeypatch, analyzer):
    # Mock _get_repo_contributors to return fake contributors
    fake_contributors = [
        {
            "login": "octocat",
            "id": 1,
            "contributions": 42,
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "html_url": "https://github.com/octocat",
            "type": "User",
            "site_admin": False,
        }
    ]
    monkeypatch.setattr(
        analyzer, "_get_repo_contributors", lambda repo: fake_contributors
    )
    # Mock _get_user_details to add more info
    monkeypatch.setattr(
        analyzer,
        "_get_user_details",
        lambda username: {
            "name": "The Octocat",
            "bio": "Loves Python and open source",
            "public_repos": 12,
            "followers": 150,
        },
    )
    contributors = analyzer.get_contributor_insights("dummy/repo")
    assert len(contributors) == 1
    c = contributors[0]
    assert c.login == "octocat"
    assert c.name == "The Octocat"
    assert "Programming" in c.skills
    assert c.expertise_score > 0
