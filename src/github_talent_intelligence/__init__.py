"""
GitHub Talent Intelligence Platform

A comprehensive platform for analyzing GitHub repositories and contributors
for AI-powered recruiting applications.
"""

from .recruiting import RecruitingIntegration
from .talent_intelligence import Contributor, Repository, TalentAnalyzer

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = ["TalentAnalyzer", "Repository", "Contributor", "RecruitingIntegration"]
