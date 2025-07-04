#!/usr/bin/env python3
"""
Test script for repository analysis functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_talent_intelligence.talent_intelligence import TalentAnalyzer

def test_repository_analysis():
    """Test the repository analysis functionality"""
    
    print("🧪 Testing Repository Analysis Functionality")
    print("=" * 50)
    
    # Test URL
    test_url = "https://github.com/chipsalliance/Caliptra"
    
    try:
        # Get GitHub token from CLI
        import subprocess
        try:
            github_token = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip()
            print(f"✅ Found GitHub token: {github_token[:10]}...")
        except:
            print("❌ Could not get GitHub token from CLI")
            return False
        
        # Initialize analyzer with token
        print("📡 Initializing TalentAnalyzer...")
        analyzer = TalentAnalyzer(github_token=github_token)
        print("✅ TalentAnalyzer initialized successfully")
        
        # Test repository analysis
        print(f"\n🔍 Analyzing repository: {test_url}")
        repositories = analyzer.analyze_repository(test_url, "full")
        
        if not repositories:
            print("❌ No repositories returned from analysis")
            return False
        
        repo = repositories[0]
        print(f"✅ Repository analysis completed successfully!")
        print(f"   Repository: {repo.full_name}")
        print(f"   Description: {repo.description}")
        print(f"   Language: {repo.language}")
        print(f"   Classification: {repo.classification}")
        print(f"   Contributors: {len(repo.contributors)}")
        print(f"   Stars: {repo.stargazers_count}")
        print(f"   Forks: {repo.forks_count}")
        
        # Show top contributors
        print(f"\n👥 Top Contributors:")
        sorted_contributors = sorted(repo.contributors, key=lambda c: c.contributions, reverse=True)
        for i, contributor in enumerate(sorted_contributors[:5]):
            print(f"   {i+1}. {contributor.login} ({contributor.name or 'N/A'})")
            print(f"      Contributions: {contributor.contributions}")
            if contributor.expertise_score is not None:
                print(f"      Expertise Score: {contributor.expertise_score:.2f}")
            else:
                print(f"      Expertise Score: N/A")
            print(f"      Skills: {', '.join(contributor.skills) if contributor.skills else 'None'}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_repository_analysis()
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Tests failed!")
        sys.exit(1) 