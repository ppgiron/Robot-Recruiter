#!/usr/bin/env python3
"""
Simple test script for GitHub OAuth device flow
"""
import sys
import os
sys.path.append('src')

from github_talent_intelligence.github_oauth import github_device_login

if __name__ == "__main__":
    print("GitHub OAuth Test")
    print("=" * 40)
    
    # Get client ID from user
    client_id = input("Enter your GitHub OAuth Client ID (or press Enter to skip OAuth): ").strip()
    
    if not client_id:
        print("Skipping OAuth flow. Using Personal Access Token directly.")
        client_id = None
    
    print(f"\nUsing Client ID: {client_id[:8] if client_id else 'None'}...")
    print("\nStarting authentication...")
    
    try:
        token = github_device_login(client_id)
        if token:
            print(f"\nSuccess! Token saved to .github_token")
            print(f"Token preview: {token[:20]}...")
        else:
            print("Authentication failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 