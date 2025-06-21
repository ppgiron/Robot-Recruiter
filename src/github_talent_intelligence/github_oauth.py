import os
import requests
import time
import webbrowser
import secrets

def github_device_login(client_id, client_secret=None, scope="repo user"):
    """
    Implements GitHub OAuth web application flow for CLI. Stores token in .github_token.
    """
    # If no client secret provided, try Personal Access Token approach
    if not client_secret:
        print("No Client Secret provided. Using Personal Access Token approach.")
        token = input("Enter your GitHub Personal Access Token: ").strip()
        if token:
            with open('.github_token', 'w') as f:
                f.write(token)
            print("GitHub token saved to .github_token.")
            return token
        else:
            print("Error: Personal Access Token is required")
            return None
    
    # Generate a random state for security
    state = secrets.token_urlsafe(32)
    
    # Use a redirect URI that doesn't require a server
    redirect_uri = "http://localhost:8000/callback"
    
    auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&scope={scope}&redirect_uri={redirect_uri}&state={state}"
    
    print(f"\nPlease visit this URL to authorize Robot Recruiter:")
    print(f"{auth_url}")
    print("\nAfter authorizing, you'll see an error page (this is expected).")
    print("Look at the URL in your browser - it will contain 'code=' and 'state=' parameters.")
    print("Copy the entire URL and paste it below.")
    
    # Try to open the browser automatically
    try:
        webbrowser.open(auth_url)
        print("(Browser should have opened automatically)")
    except:
        print("(Please copy and paste the URL into your browser)")
    
    # Get the full redirect URL from user
    redirect_url = input("\nEnter the full URL from your browser: ").strip()
    
    if not redirect_url:
        print("Error: Redirect URL is required")
        return None
    
    # Extract the authorization code from the URL
    try:
        # Parse the URL to get the code parameter
        if 'code=' in redirect_url:
            code_start = redirect_url.find('code=') + 5
            code_end = redirect_url.find('&', code_start)
            if code_end == -1:
                code_end = len(redirect_url)
            auth_code = redirect_url[code_start:code_end]
        else:
            print("Error: No authorization code found in URL")
            return None
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return None
    
    # Exchange code for token
    token_url = "https://github.com/login/oauth/access_token"
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "Robot-Recruiter/1.0"
    })
    
    resp = session.post(token_url, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    })
    
    if resp.status_code != 200:
        print(f"Error exchanging code for token: {resp.status_code}")
        print(f"Response: {resp.text}")
        return None
    
    data = resp.json()
    if 'access_token' in data:
        token = data['access_token']
        with open('.github_token', 'w') as f:
            f.write(token)
        print("\nGitHub authentication successful! Token saved to .github_token.")
        return token
    else:
        print(f"Error: {data}")
        return None 