"""Test file for GitHub Talent Intelligence Platform."""

# Add your tests here

import os
import pytest
from src.github_talent_intelligence.recruiting import RecruitingIntegration

class DummyAnalyzer:
    def analyze_organization(self, org_name, **kwargs):
        class DummyRepo:
            contributors = []
        return [DummyRepo()]

def test_discover_talent(monkeypatch):
    os.environ['GITHUB_TOKEN'] = 'dummy_token'
    integration = RecruitingIntegration(github_token='dummy_token')
    # Patch analyzer to avoid real API calls
    integration.analyzer = DummyAnalyzer()
    result = integration.discover_talent(organizations=['dummyorg'])
    assert 'candidates' in result
    assert 'summary' in result
