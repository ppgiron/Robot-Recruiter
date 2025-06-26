"""
GitHub Talent Intelligence Platform

A comprehensive platform for analyzing GitHub repositories and contributors
for AI-powered recruiting applications.
"""

from .talent_intelligence import TalentAnalyzer, Repository, Contributor
from .recruiting import RecruitingIntegration
from .token_manager import SecureTokenManager, get_github_token, get_openai_api_key

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "TalentAnalyzer",
    "Repository", 
    "Contributor",
    "RecruitingIntegration",
    "SecureTokenManager",
    "get_github_token",
    "get_openai_api_key"
]
