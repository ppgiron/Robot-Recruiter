#!/usr/bin/env python3
"""
Setup script for GitHub Talent Intelligence Platform
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="github-talent-intelligence",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive platform for analyzing GitHub repositories and contributors for AI-powered recruiting applications",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/github-talent-intelligence",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Human Resources",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Human Resources",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "talent-analyzer=talent_analyzer:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords="github, talent, intelligence, recruiting, ai, hr, blockchain, developers",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/github-talent-intelligence/issues",
        "Source": "https://github.com/yourusername/github-talent-intelligence",
        "Documentation": "https://github-talent-intelligence.readthedocs.io/",
    },
) 