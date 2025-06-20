import os
import json
import csv
import argparse
import subprocess
import requests
from dotenv import load_dotenv
import time
from collections import defaultdict

def get_gh_token():
    """Get GitHub token from GitHub CLI"""
    try:
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        print("GitHub CLI (gh) not found. Please install it or provide a token manually.")
    return None

# --- NLP / ML ---
# Lazy load NLP libraries to avoid overhead when not in use
sentence_transformers = None
sklearn_similarity = None

PROTOTYPE_DESCRIPTIONS = {
    'BlockOps': "Infrastructure as code, CI/CD pipelines, Docker containers, Kubernetes orchestration, system monitoring, and deployment automation for blockchain networks.",
    'Staking': "Code for running validator nodes, managing delegations, handling slashing events, and participating in proof-of-stake consensus and reward distribution.",
    'Protocol': "Core implementation of a blockchain protocol, including peer-to-peer networking, consensus algorithms, client specifications, and state transition logic.",
    'Hardware': "Silicon chip design, field-programmable gate arrays (FPGA), hardware description languages like Verilog or VHDL, and root of trust (RoT) implementations.",
    'Security': "Cryptographic libraries, security audits, vulnerability research, secure key management, and tools for hardening software and infrastructure.",
}

def classify_repo_nlp(repo):
    """Classifies a repo using sentence embeddings and cosine similarity."""
    global sentence_transformers, sklearn_similarity
    # Load libraries on first use
    if sentence_transformers is None:
        import sentence_transformers as st
        from sklearn.metrics.pairwise import cosine_similarity
        sentence_transformers = st
        sklearn_similarity = cosine_similarity

    model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create a comprehensive text string for the repository
    repo_text = f"{repo.get('name', '')}. {repo.get('description', '')}. Topics: {' '.join(repo.get('topics', []))}"
    
    # Generate embeddings
    repo_embedding = model.encode([repo_text])
    category_embeddings = model.encode(list(PROTOTYPE_DESCRIPTIONS.values()))
    
    # Calculate similarity
    similarities = sklearn_similarity(repo_embedding, category_embeddings)
    
    # Find the best match
    best_match_index = similarities.argmax()
    best_match_score = similarities[0, best_match_index]
    
    # You can set a threshold if desired
    if best_match_score > 0.2: # Example threshold
        return list(PROTOTYPE_DESCRIPTIONS.keys())[best_match_index]
    
    return 'Unclassified'

# --- Classification Logic ---
INDICATORS = [
    'infra', 'node', 'validator', 'iac', 'docker', 'ops', 'deployment', 'k8s', 'kubernetes', 'ci', 'cd', 'devops', 'compose', 'ansible', 'terraform', 'helm', 'cluster', 'monitor', 'prometheus', 'grafana', 'pipeline', 'automation', 'build', 'test', 'runner', 'orchestrator', 'deployment', 'infrastructure'
]

CLASSIFICATION_RULES = [
    ('BlockOps', ['infra', 'ops', 'iac', 'docker', 'deployment', 'devops', 'k8s', 'kubernetes', 'ansible', 'terraform', 'helm', 'monitor', 'prometheus', 'grafana', 'pipeline', 'automation', 'build', 'test', 'runner', 'orchestrator', 'infrastructure']),
    ('Staking', ['stake', 'staking', 'validator', 'delegat', 'slash', 'reward', 'epoch', 'attest', 'proposer', 'beacon', 'consensus']),
    ('Protocol', ['protocol', 'spec', 'node', 'client', 'chain', 'network', 'consensus', 'p2p', 'blockchain', 'eth', 'ethereum', 'filecoin', 'polkadot', 'substrate', 'libp2p', 'ssz', 'actor', 'state', 'vm', 'runtime']),
    ('Hardware', ['fpga', 'verilog', 'systemverilog', 'vhdl', 'rtl', 'silicon', 'asic', 'chip', 'board', 'hdl', 'opentitan']),
    ('Security', ['security', 'rot', 'root of trust', 'trusted', 'cryptography', 'exploit', 'vulnerability', 'hardening', 'bls', 'schnorrkel'])
]

# --- Utility Functions ---
def flag_indicators(repo):
    text = (repo.get('name', '') + ' ' + (repo.get('description') or '')).lower()
    return [ind for ind in INDICATORS if ind in text]

def categorize_file(filename):
    """Categorizes a file into a role based on its path and extension."""
    filename = filename.lower()
    # Infra check (high priority)
    if '.github/' in filename or 'dockerfile' in filename or filename.endswith(('.tf', '.yaml', '.yml', '.hcl')):
        return 'infra'
    # Docs check
    if '/docs/' in filename or filename.endswith(('.md', '.mdx', '.rst')):
        return 'docs'
    # Test check
    if 'test' in filename or 'spec' in filename or '__tests__' in filename or filename.endswith(('_test.go', '.test.js', '.spec.ts')):
        return 'test'
    # Code check (common extensions)
    code_extensions = ['.js', '.ts', '.py', '.go', '.rs', '.java', '.cs', '.cpp', '.c', '.h', '.rb', '.php', '.sol', '.zig']
    if any(filename.endswith(ext) for ext in code_extensions):
        return 'code'
    return 'other'

def classify_contributor_roles(repo, token):
    """Analyzes recent commits to classify contributor roles. WARNING: API-intensive."""
    print("  -> Classifying contributor roles (may be slow, analyzing last 100 commits)...")
    stats = defaultdict(lambda: defaultdict(int))
    
    # 1. Get the last 100 commits (stubs)
    commits_url = f"https://api.github.com/repos/{repo['full_name']}/commits?per_page=100"
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'}
    try:
        response = requests.get(commits_url, headers=headers)
        response.raise_for_status()
        commits = response.json()
    except requests.RequestException as e:
        print(f"    ! Could not fetch commits for {repo['full_name']}: {e}")
        return

    # 2. Get details for each commit
    for i, commit_stub in enumerate(commits):
        # Small delay to be nice to the API
        time.sleep(0.1)
        
        # Skip if author is null (can happen)
        if not commit_stub.get('author'):
            continue
            
        author_login = commit_stub['author']['login']
        
        try:
            response = requests.get(commit_stub['url'], headers=headers)
            response.raise_for_status()
            commit_details = response.json()
        except requests.RequestException as e:
            print(f"    ! Could not fetch commit details for {commit_stub['sha']}: {e}")
            continue

        if 'files' in commit_details:
            for file in commit_details['files']:
                category = categorize_file(file['filename'])
                stats[author_login][category] += 1
                
    # 3. Attach stats to the contributor list in the repo object
    if 'contributors' in repo and repo['contributors']:
        for contributor in repo['contributors']:
            contributor['roles'] = stats.get(contributor['login'], {})

def classify_repo_weighted(repo):
    scores = {'BlockOps': 0, 'Staking': 0, 'Protocol': 0, 'Hardware': 0, 'Security': 0}
    text_name = repo.get('name', '').lower()
    text_desc = (repo.get('description') or '').lower()
    topics = repo.get('topics', [])
    for label, keywords in CLASSIFICATION_RULES:
        for kw in keywords:
            if kw in text_name:
                scores[label] += 3
            if kw in text_desc:
                scores[label] += 2
            if any(kw in topic for topic in topics):
                scores[label] += 4
    # Use language as a signal
    language = repo.get('language')
    if language:
        lang_lower = language.lower()
        if lang_lower in ['shell', 'dockerfile', 'yaml']:
            scores['BlockOps'] += 2
        if lang_lower in ['systemverilog', 'verilog', 'vhdl']:
            scores['Hardware'] += 3 # Strong signal
            
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Unclassified'

def get_contributors(repo_full_name, token):
    """Fetches contributor data for a specific repository."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
    }
    url = f'https://api.github.com/repos/{repo_full_name}/contributors'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to fetch contributors for {repo_full_name}: {response.status_code}")
    return []

def get_user_details(username, token):
    """Fetches detailed profile information for a GitHub user."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
    }
    url = f'https://api.github.com/users/{username}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to fetch user details for {username}: {response.status_code}")
    return None

def get_repo(repo_full_name, token):
    """Fetches data for a single repository."""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
    }
    url = f'https://api.github.com/repos/{repo_full_name}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to fetch repo {repo_full_name}: {response.status_code}")
    return None

# --- GitHub API ---
def get_repos(user, token, is_org=False):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json',
    }
    per_page = 100
    page = 1
    all_repos = []
    if is_org:
        api_url = f'https://api.github.com/orgs/{user}/repos'
    else:
        api_url = f'https://api.github.com/users/{user}/repos'
    while True:
        params = {'per_page': per_page, 'page': page, 'type': 'all'}
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f'Error fetching page {page}:', response.status_code, response.text)
            break
        repos = response.json()
        if not repos:
            break
        all_repos.extend(repos)
        print(f'Fetched page {page} with {len(repos)} repos')
        page += 1
    return all_repos

def get_topics(repo_full_name, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.mercy-preview+json',
    }
    url = f'https://api.github.com/repos/{repo_full_name}/topics'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('names', [])
    return []

# --- Main Analysis Function ---
def analyze_repos(user, token, is_org=False):
    repos = get_repos(user, token, is_org)
    analyzed = []
    for i, repo in enumerate(repos, 1):
        print(f'Analyzing repo {i}/{len(repos)}: {repo["name"]}')
        # Fetch topics for more accurate classification
        repo['topics'] = get_topics(repo['full_name'], token)
        repo['indicators'] = flag_indicators(repo)
        repo['classification'] = classify_repo_weighted(repo)
        analyzed.append(repo)
    return analyzed

def analyze_repos_list(repos, token, analyze_contributors=False, use_nlp=False, classify_roles=False):
    analyzed = []
    total_repos = len(repos)
    for i, repo in enumerate(repos, 1):
        print(f'Analyzing repo {i}/{total_repos}: {repo["name"]}')
        full_repo_details = get_repo(repo['full_name'], token)
        if not full_repo_details:
            continue
        
        # Classification
        full_repo_details['topics'] = get_topics(full_repo_details['full_name'], token) # Needed for both methods
        if use_nlp:
            print("  -> Using NLP classification...")
            full_repo_details['classification'] = classify_repo_nlp(full_repo_details)
        else:
            print("  -> Using keyword classification...")
            full_repo_details['indicators'] = flag_indicators(full_repo_details)
            full_repo_details['classification'] = classify_repo_weighted(full_repo_details)

        # Contributor Analysis
        if analyze_contributors or classify_roles:
            contributors = get_contributors(full_repo_details['full_name'], token)
            full_repo_details['contributors'] = []
            total_contributors = len(contributors)
            for j, contributor in enumerate(contributors, 1):
                print(f'  -> Fetching contributor {j}/{total_contributors}: {contributor["login"]}')
                details = get_user_details(contributor['login'], token)
                if details:
                    contributor_data = {**contributor, **details}
                    full_repo_details['contributors'].append(contributor_data)
                else:
                    full_repo_details['contributors'].append(contributor)
            
            # Role Classification
            if classify_roles:
                classify_contributor_roles(full_repo_details, token)

        analyzed.append(full_repo_details)
    return analyzed

def save_to_csv(analyzed_data, base_filename):
    """Saves the analyzed data to two CSV files."""
    repo_fieldnames = [
        'full_name', 'name', 'classification', 'private', 'html_url', 'description', 
        'fork', 'url', 'created_at', 'updated_at', 'pushed_at', 'git_url', 
        'ssh_url', 'clone_url', 'homepage', 'size', 'stargazers_count', 
        'watchers_count', 'forks_count', 'open_issues_count', 'language', 
        'license', 'owner_login', 'indicators'
    ]
    contributor_fieldnames = [
        'repo_full_name', 'login', 'id', 'html_url', 'type', 'site_admin',
        'contributions', 'name', 'company', 'blog', 'location', 'email', 'hireable',
        'bio', 'twitter_username', 'public_repos', 'public_gists', 'followers', 'following', 'roles'
    ]

    repos_filepath = f"{base_filename}_repos.csv"
    contributors_filepath = f"{base_filename}_contributors.csv"

    repo_rows = []
    contributor_rows = []
    has_contributors = False

    for repo in analyzed_data:
        repo_row = {key: repo.get(key) for key in repo_fieldnames if key != 'owner_login' and key != 'license'}
        repo_row['owner_login'] = repo.get('owner', {}).get('login')
        repo_row['license'] = repo.get('license', {}).get('name')
        repo_row['indicators'] = ', '.join(repo.get('indicators', []))
        repo_rows.append(repo_row)

        if 'contributors' in repo:
            has_contributors = True
            for contributor in repo['contributors']:
                contributor_row = {key: contributor.get(key) for key in contributor_fieldnames if key != 'repo_full_name' and key != 'roles'}
                contributor_row['repo_full_name'] = repo['full_name']
                # Serialize the roles dict into a JSON string for the CSV
                contributor_row['roles'] = json.dumps(contributor.get('roles', {}))
                contributor_rows.append(contributor_row)

    with open(repos_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=repo_fieldnames)
        writer.writeheader()
        writer.writerows(repo_rows)
    print(f"Repository data saved to {repos_filepath}")

    if has_contributors:
        with open(contributors_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=contributor_fieldnames)
            writer.writeheader()
            writer.writerows(contributor_rows)
        print(f"Contributor data saved to {contributors_filepath}")

# --- CLI ---
def main():
    parser = argparse.ArgumentParser(description='Analyze and classify GitHub repos for a user, org, or a single repo.')
    parser.add_argument('user', nargs='?', default=None, help='GitHub username or org (optional if --repo is used)')
    parser.add_argument('--repo', help='Analyze a single repository (e.g., owner/repo)')
    parser.add_argument('--org', action='store_true', help='Treat user as an organization')
    parser.add_argument('--contributors', action='store_true', help='Analyze contributors and fetch their contact info')
    parser.add_argument('--nlp', action='store_true', help='Use advanced NLP for classification')
    parser.add_argument('--classify-contributors', action='store_true', help='Classify contributor roles based on recent commits (API intensive)')
    parser.add_argument('--output', default='analyzed_repos.json', help='Output JSON file base name')
    parser.add_argument('--csv', help='Export to CSV with the given base filename (e.g., my_analysis)')
    parser.add_argument('--token', default=None, help='GitHub API token (optional if gh CLI is installed)')
    args = parser.parse_args()

    if not args.user and not args.repo:
        parser.error('Either a user/org or a --repo must be specified.')
    if args.user and args.repo:
        parser.error('Cannot specify both a user/org and a --repo.')

    if args.classify_contributors:
        print("Warning: Contributor role classification is API-intensive and may be slow.")
        args.contributors = True # Implied

    # Try to get token from GitHub CLI first, then fallback to argument/env
    token = args.token or get_gh_token()
    if not token:
        raise ValueError('GitHub token required. Install GitHub CLI (gh) or provide token with --token')

    repos_to_analyze = []
    if args.repo:
        print(f"Analyzing single repository: {args.repo}")
        repo_data = get_repo(args.repo, token)
        if repo_data:
            repos_to_analyze.append(repo_data)
    elif args.user:
        print(f'Analyzing repositories for {"organization" if args.org else "user"} {args.user}...')
        repos_to_analyze = get_repos(args.user, token, is_org=args.org)

    analyzed = analyze_repos_list(
        repos_to_analyze, 
        token, 
        analyze_contributors=args.contributors, 
        use_nlp=args.nlp,
        classify_roles=args.classify_contributors
    )
    
    # JSON Output (always runs)
    json_output_path = f"{args.output.replace('.json', '')}.json"
    with open(json_output_path, 'w') as f:
        json.dump(analyzed, f, indent=2)
    
    # CSV Output (optional)
    if args.csv:
        save_to_csv(analyzed, args.csv)

    # Print summary
    classifications = {}
    for repo in analyzed:
        class_type = repo['classification']
        classifications[class_type] = classifications.get(class_type, 0) + 1
    
    print(f'\nAnalysis complete! Found {len(analyzed)} repositories.')
    print('\nClassification Summary:')
    for class_type, count in classifications.items():
        print(f'{class_type}: {count} repos')
    
    print(f'\nDetailed JSON results written to {json_output_path}')

if __name__ == '__main__':
    main() 