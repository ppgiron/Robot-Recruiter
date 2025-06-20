#!/usr/bin/env python3
"""
Migration script to transition from the old project structure
to the new GitHub Talent Intelligence Platform.
"""

import os
import json
import shutil
from pathlib import Path


def migrate_project():
    """Migrate the project to the new structure."""
    
    print("🔄 GitHub Talent Intelligence Platform Migration")
    print("=" * 50)
    
    # Create backup of old files
    print("\n1. Creating backup of old files...")
    backup_dir = "backup_old_project"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    old_files = [
        "repo_analyzer.py",
        "scrape_chainsafe_repos.py",
        "analyzed_repos.json",
        "lodestar_analysis.json",
        "opentitan_analysis.json",
        "opentitan_analysis_v2.json",
        "opentitan_analysis_nlp.json"
    ]
    
    for file in old_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"   ✓ Backed up {file}")
    
    # Archive old CSV files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if csv_files:
        csv_backup_dir = os.path.join(backup_dir, "csv_files")
        os.makedirs(csv_backup_dir, exist_ok=True)
        for csv_file in csv_files:
            shutil.copy2(csv_file, csv_backup_dir)
            print(f"   ✓ Backed up {csv_file}")
    
    print(f"   Backup created in: {backup_dir}")
    
    # Create new directory structure
    print("\n2. Creating new directory structure...")
    
    directories = [
        "src",
        "src/github_talent_intelligence",
        "tests",
        "docs",
        "examples",
        "data"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✓ Created {directory}")
    
    # Move and rename files
    print("\n3. Moving files to new structure...")
    
    # Move main modules
    if os.path.exists("talent_intelligence.py"):
        shutil.move("talent_intelligence.py", "src/github_talent_intelligence/__init__.py")
        print("   ✓ Moved talent_intelligence.py to src/github_talent_intelligence/__init__.py")
    
    if os.path.exists("recruiting_integration.py"):
        shutil.move("recruiting_integration.py", "src/github_talent_intelligence/recruiting.py")
        print("   ✓ Moved recruiting_integration.py to src/github_talent_intelligence/recruiting.py")
    
    # Move CLI
    if os.path.exists("talent_analyzer.py"):
        shutil.move("talent_analyzer.py", "src/github_talent_intelligence/cli.py")
        print("   ✓ Moved talent_analyzer.py to src/github_talent_intelligence/cli.py")
    
    # Move example
    if os.path.exists("example_integration.py"):
        shutil.move("example_integration.py", "examples/ai_recruiting_integration.py")
        print("   ✓ Moved example_integration.py to examples/ai_recruiting_integration.py")
    
    # Move configuration
    if os.path.exists("config.yaml"):
        shutil.move("config.yaml", "src/github_talent_intelligence/config.yaml")
        print("   ✓ Moved config.yaml to src/github_talent_intelligence/config.yaml")
    
    # Move data files
    data_files = [f for f in os.listdir('.') if f.endswith(('.json', '.csv'))]
    for data_file in data_files:
        shutil.move(data_file, "data/")
        print(f"   ✓ Moved {data_file} to data/")
    
    # Create __init__.py files
    print("\n4. Creating package structure...")
    
    init_files = [
        "src/__init__.py",
        "src/github_talent_intelligence/__init__.py",
        "tests/__init__.py",
        "examples/__init__.py"
    ]
    
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write('"""Package initialization."""\n')
        print(f"   ✓ Created {init_file}")
    
    # Update imports in moved files
    print("\n5. Updating imports...")
    
    # Update recruiting.py imports
    recruiting_file = "src/github_talent_intelligence/recruiting.py"
    if os.path.exists(recruiting_file):
        with open(recruiting_file, 'r') as f:
            content = f.read()
        
        # Update import
        content = content.replace(
            "from talent_intelligence import TalentAnalyzer, Repository, Contributor",
            "from . import TalentAnalyzer, Repository, Contributor"
        )
        
        with open(recruiting_file, 'w') as f:
            f.write(content)
        print("   ✓ Updated imports in recruiting.py")
    
    # Update CLI imports
    cli_file = "src/github_talent_intelligence/cli.py"
    if os.path.exists(cli_file):
        with open(cli_file, 'r') as f:
            content = f.read()
        
        # Update import
        content = content.replace(
            "from talent_intelligence import TalentAnalyzer",
            "from . import TalentAnalyzer"
        )
        
        with open(cli_file, 'w') as f:
            f.write(content)
        print("   ✓ Updated imports in cli.py")
    
    # Create new main __init__.py
    print("\n6. Creating main package __init__.py...")
    
    main_init_content = '''"""
GitHub Talent Intelligence Platform

A comprehensive platform for analyzing GitHub repositories and contributors
for AI-powered recruiting applications.
"""

from .talent_intelligence import TalentAnalyzer, Repository, Contributor
from .recruiting import RecruitingIntegration

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "TalentAnalyzer",
    "Repository", 
    "Contributor",
    "RecruitingIntegration"
]
'''
    
    with open("src/github_talent_intelligence/__init__.py", 'w') as f:
        f.write(main_init_content)
    print("   ✓ Created main package __init__.py")
    
    # Create test files
    print("\n7. Creating test structure...")
    
    test_files = [
        "tests/test_talent_intelligence.py",
        "tests/test_recruiting_integration.py",
        "tests/conftest.py"
    ]
    
    for test_file in test_files:
        with open(test_file, 'w') as f:
            f.write('"""Test file for GitHub Talent Intelligence Platform."""\n\n')
            f.write('# Add your tests here\n')
        print(f"   ✓ Created {test_file}")
    
    # Create documentation
    print("\n8. Creating documentation...")
    
    docs_files = [
        "docs/installation.md",
        "docs/usage.md", 
        "docs/api.md",
        "docs/integration.md"
    ]
    
    for doc_file in docs_files:
        with open(doc_file, 'w') as f:
            f.write(f"# {os.path.basename(doc_file).replace('.md', '').title()}\n\n")
            f.write("Documentation for this section.\n")
        print(f"   ✓ Created {doc_file}")
    
    # Create .gitignore
    print("\n9. Creating .gitignore...")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
data/*.json
data/*.csv
results/
*.log
backup_old_project/

# Testing
.coverage
.pytest_cache/
htmlcov/

# Documentation
docs/_build/
"""
    
    with open(".gitignore", 'w') as f:
        f.write(gitignore_content)
    print("   ✓ Created .gitignore")
    
    # Create Makefile for common tasks
    print("\n10. Creating Makefile...")
    
    makefile_content = """# GitHub Talent Intelligence Platform Makefile

.PHONY: install test lint format docs clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

docs:
	cd docs && make html

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

setup:
	python talent_analyzer.py setup

analyze-example:
	python talent_analyzer.py analyze --org ChainSafe --output results

run-example:
	python examples/ai_recruiting_integration.py
"""
    
    with open("Makefile", 'w') as f:
        f.write(makefile_content)
    print("   ✓ Created Makefile")
    
    # Final instructions
    print("\n✅ Migration Complete!")
    print("\n📋 Next Steps:")
    print("1. Install the package: make install")
    print("2. Set up your GitHub token: export GITHUB_TOKEN=your_token")
    print("3. Run the setup: make setup")
    print("4. Test the installation: make analyze-example")
    print("5. Try the AI recruiting integration: make run-example")
    print("\n📁 New Project Structure:")
    print("src/github_talent_intelligence/  - Main package")
    print("examples/                       - Integration examples")
    print("tests/                          - Test files")
    print("docs/                           - Documentation")
    print("data/                           - Data files")
    print("backup_old_project/             - Backup of old files")
    
    print("\n🔧 Available Commands:")
    print("make install      - Install the package")
    print("make test         - Run tests")
    print("make lint         - Run linting")
    print("make format       - Format code")
    print("make setup        - Interactive setup")
    print("make analyze-example - Analyze example organization")
    print("make run-example  - Run AI recruiting integration example")


if __name__ == '__main__':
    migrate_project() 