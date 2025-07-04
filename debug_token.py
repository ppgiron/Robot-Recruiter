#!/usr/bin/env python3
"""
Debug script to test GitHub token retrieval
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from github_talent_intelligence.token_manager import SecureTokenManager
import requests

def test_token():
    print("🔍 Testing GitHub Token Retrieval")
    print("=" * 40)
    
    try:
        # Test token manager
        print("📡 Testing SecureTokenManager...")
        token_manager = SecureTokenManager()
        
        try:
            token = token_manager.get_github_token()
            print(f"✅ Token retrieved: {token[:10]}...")
        except Exception as e:
            print(f"❌ Failed to get token: {e}")
            return False
        
        # Test GitHub API call
        print("\n🌐 Testing GitHub API call...")
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github+json',
        }
        
        # Test with a simple API call
        response = requests.get('https://api.github.com/user', headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ API call successful! User: {user_data.get('login', 'Unknown')}")
            
            # Test repository API call
            print("\n📦 Testing repository API call...")
            repo_response = requests.get('https://api.github.com/repos/chipsalliance/Caliptra', headers=headers)
            print(f"Repository status code: {repo_response.status_code}")
            
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                print(f"✅ Repository API call successful!")
                print(f"   Repository: {repo_data.get('full_name')}")
                print(f"   Description: {repo_data.get('description')}")
                print(f"   Language: {repo_data.get('language')}")
                return True
            else:
                print(f"❌ Repository API call failed: {repo_response.text}")
                return False
        else:
            print(f"❌ API call failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_token()
    if success:
        print("\n🎉 Token test passed!")
        sys.exit(0)
    else:
        print("\n💥 Token test failed!")
        sys.exit(1) 