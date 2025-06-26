"""
GitHub Talent Intelligence Platform
A comprehensive solution for analyzing GitHub repositories and contributors
for AI-powered recruiting applications.
"""

import csv
import json
import os
import subprocess
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import yaml
from dotenv import load_dotenv
from tqdm import tqdm

from .config_loader import load_categories
from .gpt_stub import get_chatgpt_suggestion
from .token_manager import SecureTokenManager

# Lazy load NLP libraries
sentence_transformers = None
sklearn_similarity = None


@dataclass
class Contributor:
    """Represents a GitHub contributor with enhanced metadata."""

    login: str
    id: int
    contributions: int
    avatar_url: str
    html_url: str
    type: str
    site_admin: bool
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    twitter_username: Optional[str] = None
    public_repos: Optional[int] = None
    public_gists: Optional[int] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    roles: Optional[Dict[str, int]] = None
    skills: Optional[List[str]] = None
    expertise_score: Optional[float] = None
    api_data: Optional[dict] = None


@dataclass
class Repository:
    """Represents a GitHub repository with analysis results."""

    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    topics: List[str]
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    size: int
    created_at: str
    updated_at: str
    pushed_at: str
    classification: str
    indicators: List[str]
    contributors: List[Contributor]
    analysis_score: Optional[float] = None
    api_data: Optional[dict] = None
    analysis_confidence: Optional[float] = None


class TalentAnalyzer:
    """
    Main class for analyzing GitHub repositories and contributors
    for talent intelligence and recruiting purposes.
    """

    def __init__(
        self, github_token: Optional[str] = None, config_path: Optional[str] = None
    ):
        """
        Initialize the TalentAnalyzer.

        Args:
            github_token: GitHub API token
            config_path: Path to configuration file
        """
        # Use provided token or get from secure sources
        if github_token:
            self.github_token = github_token
        else:
            # Use secure token manager with 1Password integration
            token_manager = SecureTokenManager()
            self.github_token = token_manager.get_github_token()
        
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github+json",
            }
        )

        # Load categories and keywords from config
        self.categories = load_categories(config_path)

        # Classification categories
        self.classification_rules = [
            (
                "BlockOps",
                [
                    "infra",
                    "ops",
                    "iac",
                    "docker",
                    "deployment",
                    "devops",
                    "k8s",
                    "kubernetes",
                    "ansible",
                    "terraform",
                    "helm",
                    "monitor",
                    "prometheus",
                    "grafana",
                    "pipeline",
                    "automation",
                    "build",
                    "test",
                    "runner",
                    "orchestrator",
                    "infrastructure",
                ],
            ),
            (
                "Staking",
                [
                    "stake",
                    "staking",
                    "validator",
                    "delegat",
                    "slash",
                    "reward",
                    "epoch",
                    "attest",
                    "proposer",
                    "beacon",
                    "consensus",
                ],
            ),
            (
                "Protocol",
                [
                    "protocol",
                    "spec",
                    "node",
                    "client",
                    "chain",
                    "network",
                    "consensus",
                    "p2p",
                    "blockchain",
                    "eth",
                    "ethereum",
                    "filecoin",
                    "polkadot",
                    "substrate",
                    "libp2p",
                    "ssz",
                    "actor",
                    "state",
                    "vm",
                    "runtime",
                ],
            ),
            (
                "Hardware",
                [
                    "fpga",
                    "verilog",
                    "systemverilog",
                    "vhdl",
                    "rtl",
                    "silicon",
                    "asic",
                    "chip",
                    "board",
                    "hdl",
                    "opentitan",
                ],
            ),
            (
                "Security",
                [
                    "security",
                    "rot",
                    "root of trust",
                    "trusted",
                    "cryptography",
                    "exploit",
                    "vulnerability",
                    "hardening",
                    "bls",
                    "schnorrkel",
                ],
            ),
        ]

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "github": {"rate_limit_delay": 0.1, "max_retries": 3},
            "analysis": {
                "use_nlp": True,
                "classify_roles": True,
                "max_commits_per_repo": 100,
                "max_contributors_per_repo": 50,
            },
            "categories": {"custom_keywords": []},
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                self._merge_configs(default_config, user_config)

        return default_config

    def _merge_configs(self, default: Dict, user: Dict):
        """Recursively merge user config with defaults."""
        for key, value in user.items():
            if (
                key in default
                and isinstance(default[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_configs(default[key], value)
            else:
                default[key] = value

    def analyze_organization(self, org_name: str, **kwargs) -> List[Repository]:
        """
        Analyze all repositories in a GitHub organization.

        Args:
            org_name: Name of the GitHub organization
            **kwargs: Additional analysis options

        Returns:
            List of analyzed repositories
        """
        print(f"Analyzing organization: {org_name}")

        # Get all repositories
        repos_data = self._get_organization_repos(org_name)
        print(f"Found {len(repos_data)} repositories")

        # Analyze repositories
        return self.analyze_repositories(repos_data, **kwargs)

    def analyze_repositories(
        self, repos_data: List[Dict], **kwargs
    ) -> List[Repository]:
        """
        Analyze a list of repositories.

        Args:
            repos_data: List of repository data from GitHub API
            **kwargs: Analysis options

        Returns:
            List of analyzed repositories
        """
        use_nlp = kwargs.get("use_nlp", self.config["analysis"]["use_nlp"])
        classify_roles = kwargs.get(
            "classify_roles", self.config["analysis"]["classify_roles"]
        )

        analyzed_repos = []
        CONFIDENCE_THRESHOLD = 0.9

        for repo_data in tqdm(repos_data, desc="Analyzing repositories"):
            try:
                # Get additional repository data
                repo_full = self._get_repo_details(repo_data["full_name"])
                if not repo_full:
                    continue

                # Get topics
                topics = self._get_repo_topics(repo_data["full_name"])
                repo_full["topics"] = topics

                # Get contributors
                contributors_data = self._get_repo_contributors(repo_data["full_name"])
                contributors = []

                for contrib_data in contributors_data[
                    : self.config["analysis"]["max_contributors_per_repo"]
                ]:
                    user_details = self._get_user_details(contrib_data["login"])
                    if user_details:
                        contrib_data.update(user_details)
                    valid_keys = {f.name for f in dataclass_fields(Contributor)}
                    filtered_contrib = {
                        k: v for k, v in contrib_data.items() if k in valid_keys
                    }
                    contributor = Contributor(**filtered_contrib, api_data=contrib_data)
                    contributors.append(contributor)

                # Classify repository
                if use_nlp:
                    classification, confidence = self._classify_repo_nlp(repo_full)
                else:
                    classification, confidence = self._classify_repo_weighted(repo_full)

                # Fallback to ChatGPT if confidence is low (temporarily disabled)
                # if confidence < CONFIDENCE_THRESHOLD:
                #     prompt = (
                #         f"Classify the following GitHub repository into one of these categories: {', '.join(self.categories.keys())}.\n"
                #         f"Repository name: {repo_full.get('name', '')}\n"
                #         f"Description: {repo_full.get('description', '')}\n"
                #         f"Topics: {', '.join(repo_full.get('topics', []))}\n"
                #         f"Language: {repo_full.get('language', '')}\n"
                #         f"Respond with only the category name."
                #     )
                #     chatgpt_category = get_chatgpt_suggestion(prompt)
                #     if chatgpt_category and chatgpt_category in self.categories:
                #         classification = chatgpt_category
                #         confidence = CONFIDENCE_THRESHOLD  # Assign threshold as confidence for LLM
                #     elif chatgpt_category:
                #         classification = chatgpt_category.strip()
                #         confidence = CONFIDENCE_THRESHOLD

                # Get indicators
                indicators = self._get_indicators(repo_full)

                # Classify contributor roles if requested
                if classify_roles and contributors:
                    self._classify_contributor_roles(repo_full, contributors)

                # Create repository object
                repo = Repository(
                    name=repo_full["name"],
                    full_name=repo_full["full_name"],
                    description=repo_full.get("description"),
                    language=repo_full.get("language"),
                    topics=repo_full.get("topics", []),
                    stargazers_count=repo_full["stargazers_count"],
                    forks_count=repo_full["forks_count"],
                    open_issues_count=repo_full["open_issues_count"],
                    size=repo_full["size"],
                    created_at=repo_full["created_at"],
                    updated_at=repo_full["updated_at"],
                    pushed_at=repo_full["pushed_at"],
                    classification=classification,
                    indicators=indicators,
                    contributors=contributors,
                    api_data=repo_full,
                    analysis_confidence=confidence,
                )

                analyzed_repos.append(repo)

                # Rate limiting
                time.sleep(self.config["github"]["rate_limit_delay"])

            except Exception as e:
                print(f"Error analyzing {repo_data['full_name']}: {e}")
                continue

        return analyzed_repos

    def get_contributor_insights(self, repo_full_name: str) -> List[Contributor]:
        """
        Get detailed insights about contributors to a specific repository.

        Args:
            repo_full_name: Repository in format 'owner/repo'

        Returns:
            List of contributors with detailed insights
        """
        contributors_data = self._get_repo_contributors(repo_full_name)
        contributors = []

        for contrib_data in contributors_data:
            user_details = self._get_user_details(contrib_data["login"])
            if user_details:
                contrib_data.update(user_details)
            skills = self._analyze_contributor_skills(contrib_data)
            expertise_score = self._calculate_expertise_score(contrib_data)
            valid_keys = {f.name for f in dataclass_fields(Contributor)}
            filtered_contrib = {
                k: v for k, v in contrib_data.items() if k in valid_keys
            }
            contributor = Contributor(
                **filtered_contrib,
                skills=skills,
                expertise_score=expertise_score,
                api_data=contrib_data,
            )
            contributors.append(contributor)

        return contributors

    def export_for_recruiting(self, repositories: List[Repository]) -> Dict[str, Any]:
        """
        Export analysis results in a format optimized for AI recruiting platforms.

        Args:
            repositories: List of analyzed repositories

        Returns:
            Dictionary with recruiting-optimized data
        """
        # Extract all unique contributors
        all_contributors = {}
        for repo in repositories:
            for contributor in repo.contributors:
                if contributor.login not in all_contributors:
                    all_contributors[contributor.login] = contributor
                else:
                    # Merge data from multiple repositories
                    existing = all_contributors[contributor.login]
                    existing.contributions += contributor.contributions
                    if contributor.roles:
                        if existing.roles is None:
                            existing.roles = {}
                        for role, count in contributor.roles.items():
                            existing.roles[role] = existing.roles.get(role, 0) + count

        # Create recruiting-optimized structure
        recruiting_data = {
            "summary": {
                "total_repositories": len(repositories),
                "total_contributors": len(all_contributors),
                "categories": self._get_category_summary(repositories),
                "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "contributors": [
                {
                    "login": c.login,
                    "name": c.name,
                    "bio": c.bio,
                    "location": c.location,
                    "company": c.company,
                    "contributions": c.contributions,
                    "followers": c.followers,
                    "public_repos": c.public_repos,
                    "skills": c.skills or [],
                    "expertise_score": c.expertise_score,
                    "roles": c.roles or {},
                    "repositories": [
                        {
                            "name": repo.name,
                            "full_name": repo.full_name,
                            "classification": repo.classification,
                            "language": repo.language,
                        }
                        for repo in repositories
                        if any(
                            contrib.login == c.login for contrib in repo.contributors
                        )
                    ],
                }
                for c in all_contributors.values()
            ],
            "repositories": [
                {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "classification": repo.classification,
                    "language": repo.language,
                    "topics": repo.topics,
                    "stargazers_count": repo.stargazers_count,
                    "contributor_count": len(repo.contributors),
                }
                for repo in repositories
            ],
        }

        return recruiting_data

    def save_results(
        self,
        repositories: List[Repository],
        output_dir: str,
        formats: List[str] = ["json", "csv", "recruiting"],
    ):
        """
        Save analysis results in multiple formats.

        Args:
            repositories: List of analyzed repositories
            output_dir: Directory to save results
            formats: List of formats to export ('json', 'csv', 'recruiting')
        """
        os.makedirs(output_dir, exist_ok=True)

        if "json" in formats:
            self._save_json(repositories, output_dir)

        if "csv" in formats:
            self._save_csv(repositories, output_dir)

        if "recruiting" in formats:
            recruiting_data = self.export_for_recruiting(repositories)
            with open(os.path.join(output_dir, "recruiting_data.json"), "w") as f:
                json.dump(recruiting_data, f, indent=2, default=str)

    # Private methods for GitHub API interactions
    def _get_organization_repos(self, org_name: str) -> List[Dict]:
        """Get all repositories for an organization."""
        repos = []
        page = 1

        while True:
            url = f"https://api.github.com/orgs/{org_name}/repos"
            params = {"per_page": 100, "page": page}

            response = self.session.get(url, params=params)
            if response.status_code != 200:
                break

            page_repos = response.json()
            if not page_repos:
                break

            repos.extend(page_repos)
            page += 1

        return repos

    def _get_repo_details(self, repo_full_name: str) -> Optional[Dict]:
        """Get detailed repository information."""
        url = f"https://api.github.com/repos/{repo_full_name}"
        response = self.session.get(url)

        if response.status_code == 200:
            return response.json()
        return None

    def _get_repo_topics(self, repo_full_name: str) -> List[str]:
        """Get repository topics."""
        url = f"https://api.github.com/repos/{repo_full_name}/topics"
        response = self.session.get(url)

        if response.status_code == 200:
            return response.json().get("names", [])
        return []

    def _get_repo_contributors(self, repo_full_name: str) -> List[Dict]:
        """Get repository contributors."""
        url = f"https://api.github.com/repos/{repo_full_name}/contributors"
        response = self.session.get(url)

        if response.status_code == 200:
            return response.json()
        return []

    def _get_user_details(self, username: str) -> Optional[Dict]:
        """Get detailed user information."""
        url = f"https://api.github.com/users/{username}"
        response = self.session.get(url)

        if response.status_code == 200:
            return response.json()
        return None

    # Classification methods
    def _classify_repo_nlp(self, repo: Dict) -> Tuple[str, float]:
        """Classify repository using NLP/sentence embeddings."""
        global sentence_transformers, sklearn_similarity
        if sentence_transformers is None:
            import sentence_transformers as st
            from sklearn.metrics.pairwise import cosine_similarity

            sentence_transformers = st
            sklearn_similarity = cosine_similarity
        model = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
        repo_text = f"{repo.get('name', '')}. {repo.get('description', '')}. Topics: {' '.join(repo.get('topics', []))}"
        # Use category descriptions if available, else join keywords
        category_texts = [
            v.get("description") or " ".join(v.get("keywords", []))
            for v in self.categories.values()
        ]
        category_names = list(self.categories.keys())
        repo_embedding = model.encode([repo_text])
        category_embeddings = model.encode(category_texts)
        similarities = sklearn_similarity(repo_embedding, category_embeddings)
        best_match_index = similarities.argmax()
        best_match_score = float(similarities[0, best_match_index])
        if best_match_score > 0.2:
            return category_names[best_match_index], best_match_score
        return "Unclassified", best_match_score

    def _classify_repo_weighted(self, repo: Dict) -> Tuple[str, float]:
        """Classify repository using weighted keyword matching from config."""
        scores = {category: 0 for category in self.categories.keys()}
        text_name = repo.get("name", "").lower()
        text_desc = (repo.get("description") or "").lower()
        topics = repo.get("topics", [])
        for label, cat in self.categories.items():
            keywords = cat.get("keywords", [])
            for kw in keywords:
                if kw in text_name:
                    scores[label] += 3
                if kw in text_desc:
                    scores[label] += 2
                if any(kw in topic for topic in topics):
                    scores[label] += 4
        # Language-based signals (optional: can be extended)
        language = repo.get("language")
        if language:
            lang_lower = language.lower()
            if lang_lower in ["shell", "dockerfile", "yaml"]:
                if "DevOps" in scores:
                    scores["DevOps"] += 2
            if lang_lower in ["systemverilog", "verilog", "vhdl"]:
                if "Hardware" in scores:
                    scores["Hardware"] += 3
        best = max(scores, key=scores.get)
        best_score = scores[best]
        total_score = sum(scores.values()) or 1  # avoid division by zero
        confidence = best_score / total_score
        # Only assign if score is above threshold (e.g., 3)
        return (best if best_score > 3 else "Unclassified", confidence)

    def _get_indicators(self, repo: Dict) -> List[str]:
        """Get technical indicators from repository."""
        indicators = [
            "infra",
            "node",
            "validator",
            "iac",
            "docker",
            "ops",
            "deployment",
            "k8s",
            "kubernetes",
            "ci",
            "cd",
            "devops",
            "compose",
            "ansible",
            "terraform",
            "helm",
            "cluster",
            "monitor",
            "prometheus",
            "grafana",
            "pipeline",
            "automation",
            "build",
            "test",
            "runner",
            "orchestrator",
        ]

        text = (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
        return [ind for ind in indicators if ind in text]

    def _classify_contributor_roles(self, repo: Dict, contributors: List[Contributor]):
        """Classify contributor roles based on commit analysis."""
        # This is a simplified version - in practice, you'd analyze actual commits
        for contributor in contributors:
            # Placeholder role classification
            contributor.roles = {
                "code": contributor.contributions // 10,
                "docs": contributor.contributions // 20,
                "test": contributor.contributions // 30,
            }

    def _analyze_contributor_skills(self, contributor_data: Dict) -> List[str]:
        """Analyze contributor skills based on available data."""
        skills = []

        # Add skills based on bio and other fields
        bio = contributor_data.get("bio", "").lower()
        if any(word in bio for word in ["python", "javascript", "go", "rust", "java"]):
            skills.extend(["Programming"])

        if contributor_data.get("public_repos", 0) > 10:
            skills.append("Open Source Contributor")

        if contributor_data.get("followers", 0) > 100:
            skills.append("Community Leader")

        return skills

    def _calculate_expertise_score(self, contributor_data: Dict) -> float:
        """Calculate expertise score for a contributor."""
        score = 0.0

        # Base score from contributions
        score += min(contributor_data.get("contributions", 0) / 100, 1.0)

        # Bonus for public repos
        score += min(contributor_data.get("public_repos", 0) / 50, 0.5)

        # Bonus for followers (social proof)
        score += min(contributor_data.get("followers", 0) / 1000, 0.3)

        return min(score, 1.0)

    def _get_category_summary(self, repositories: List[Repository]) -> Dict[str, int]:
        """Get summary of repository categories."""
        summary = defaultdict(int)
        for repo in repositories:
            summary[repo.classification] += 1
        return dict(summary)

    def _save_json(self, repositories: List[Repository], output_dir: str):
        """Save results as JSON."""
        data = []
        for repo in repositories:
            repo_dict = asdict(repo)
            repo_dict["contributors"] = [asdict(c) for c in repo.contributors]
            data.append(repo_dict)

        with open(os.path.join(output_dir, "analysis_results.json"), "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _save_csv(self, repositories: List[Repository], output_dir: str):
        """Save results as CSV files matching the reference format."""
        import csv

        os.makedirs(output_dir, exist_ok=True)

        # Reference repo columns
        repo_columns = [
            "full_name",
            "name",
            "classification",
            "private",
            "html_url",
            "description",
            "fork",
            "url",
            "created_at",
            "updated_at",
            "pushed_at",
            "git_url",
            "ssh_url",
            "clone_url",
            "homepage",
            "size",
            "stargazers_count",
            "watchers_count",
            "forks_count",
            "open_issues_count",
            "language",
            "license",
            "owner_login",
            "indicators",
        ]
        # Reference contributor columns
        contrib_columns = [
            "repo_full_name",
            "login",
            "id",
            "html_url",
            "type",
            "site_admin",
            "contributions",
            "name",
            "company",
            "blog",
            "location",
            "email",
            "hireable",
            "bio",
            "twitter_username",
            "public_repos",
            "public_gists",
            "followers",
            "following",
            "roles",
        ]

        # Save repositories.csv
        repo_path = os.path.join(output_dir, "repositories.csv")
        with open(repo_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=repo_columns)
            writer.writeheader()
            for repo in repositories:
                api = repo.api_data or {}
                row = {
                    col: (api.get(col) if col in api else getattr(repo, col, ""))
                    for col in repo_columns
                }
                # Special handling for indicators (list)
                row["indicators"] = (
                    ",".join(repo.indicators)
                    if repo.indicators
                    else api.get("indicators", "")
                )
                # Special handling for license (stringified dict)
                if "license" in api and api["license"] is not None:
                    row["license"] = str(api["license"])
                writer.writerow(row)

        # Save contributors.csv
        contrib_path = os.path.join(output_dir, "contributors.csv")
        with open(contrib_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=contrib_columns)
            writer.writeheader()
            for repo in repositories:
                for c in repo.contributors:
                    api = c.api_data or {}
                    row = {
                        col: (api.get(col) if col in api else getattr(c, col, ""))
                        for col in contrib_columns
                    }
                    row["repo_full_name"] = repo.full_name
                    writer.writerow(row)

    def analyze_specific_repos(self, repo_full_names: list, **kwargs):
        """
        Analyze specific repositories by their full names (owner/repo).
        Args:
            repo_full_names: List of repository full names (e.g., ['owner/repo'])
            **kwargs: Additional analysis options
        Returns:
            List of analyzed Repository objects
        """
        repos_data = []
        for full_name in repo_full_names:
            repo_data = self._get_repo_details(full_name)
            if repo_data:
                repos_data.append(repo_data)
        return self.analyze_repositories(repos_data, **kwargs)
