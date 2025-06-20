import os
import requests
import json
from dotenv import load_dotenv

# Load GitHub token from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    raise ValueError('GITHUB_TOKEN not found in environment variables or .env file.')

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json',
}

ORG = 'ChainSafe'
PER_PAGE = 100  # Max allowed by GitHub
API_URL = f'https://api.github.com/orgs/{ORG}/repos'

INDICATORS = [
    'infra', 'node', 'validator', 'iac', 'docker', 'ops', 'deployment', 'k8s', 'kubernetes', 'ci', 'cd', 'devops', 'compose', 'ansible', 'terraform', 'helm', 'cluster', 'monitor', 'prometheus', 'grafana', 'pipeline', 'automation', 'build', 'test', 'runner', 'orchestrator', 'deployment', 'infrastructure'
]

# Simple keyword-based classification rules
CLASSIFICATION_RULES = [
    ('BlockOps', ['infra', 'ops', 'iac', 'docker', 'deployment', 'devops', 'k8s', 'kubernetes', 'ansible', 'terraform', 'helm', 'monitor', 'prometheus', 'grafana', 'pipeline', 'automation', 'build', 'test', 'runner', 'orchestrator', 'infrastructure']),
    ('Staking', ['stake', 'staking', 'validator', 'delegat', 'slash', 'reward', 'epoch', 'attest', 'proposer', 'beacon', 'consensus']),
    ('Protocol', ['protocol', 'spec', 'node', 'client', 'chain', 'network', 'consensus', 'p2p', 'blockchain', 'eth', 'ethereum', 'filecoin', 'polkadot', 'substrate', 'libp2p', 'ssz', 'actor', 'state', 'vm', 'runtime'])
]

def flag_indicators(repo):
    text = (repo.get('name', '') + ' ' + (repo.get('description') or '')).lower()
    return [ind for ind in INDICATORS if ind in text]

def classify_repo(repo):
    text = (repo.get('name', '') + ' ' + (repo.get('description') or '')).lower()
    for label, keywords in CLASSIFICATION_RULES:
        if any(kw in text for kw in keywords):
            return label
    return 'Unclassified'

all_repos = []
page = 1

while True:
    params = {'per_page': PER_PAGE, 'page': page}
    response = requests.get(API_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f'Error fetching page {page}:', response.status_code, response.text)
        break
    repos = response.json()
    if not repos:
        print(f'No more repos found at page {page}. Stopping.')
        break
    for repo in repos:
        repo['indicators'] = flag_indicators(repo)
        repo['classification'] = classify_repo(repo)
    all_repos.extend(repos)
    print(f'Fetched page {page} with {len(repos)} repos.')
    page += 1

output_path = os.path.join(os.path.dirname(__file__), 'chainsafe_repos.json')
with open(output_path, 'w') as f:
    json.dump(all_repos, f, indent=2)

print(f'Total repos fetched: {len(all_repos)}')
print(f'All metadata written to {output_path}') 