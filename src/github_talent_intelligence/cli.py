#!/usr/bin/env python3
"""
GitHub Talent Intelligence Platform - CLI Interface
Command-line tool for analyzing GitHub repositories and contributors.
"""

import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
load_dotenv()

from . import TalentAnalyzer


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """GitHub Talent Intelligence Platform - Analyze repositories and contributors for AI recruiting."""
    pass


@cli.command()
@click.option("--org", help="GitHub organization name to analyze")
@click.option("--user", help="GitHub username to analyze")
@click.option(
    "--repos", help="Comma-separated list of repositories (owner/repo format)"
)
@click.option("--output", default="results", help="Output directory for results")
@click.option(
    "--formats", default="json,csv,recruiting", help="Output formats (comma-separated)"
)
@click.option("--use-nlp/--no-nlp", default=True, help="Use NLP classification")
@click.option(
    "--classify-roles/--no-classify-roles",
    default=True,
    help="Classify contributor roles",
)
@click.option("--config", help="Path to configuration file")
def analyze(org, user, repos, output, formats, use_nlp, classify_roles, config):
    """Analyze GitHub repositories and contributors."""

    # Validate inputs
    if not any([org, user, repos]):
        click.echo("Error: Must specify either --org, --user, or --repos", err=True)
        sys.exit(1)

    try:
        # Initialize analyzer
        analyzer = TalentAnalyzer(config_path=config)

        # Parse output formats
        format_list = [f.strip() for f in formats.split(",")]

        if org:
            click.echo(f"Analyzing organization: {org}")
            repositories = analyzer.analyze_organization(
                org, use_nlp=use_nlp, classify_roles=classify_roles
            )
        elif user:
            click.echo(f"Analyzing user: {user}")
            # Get user's repositories
            repos_data = analyzer._get_user_repos(user)
            repositories = analyzer.analyze_repositories(
                repos_data, use_nlp=use_nlp, classify_roles=classify_roles
            )
        else:
            click.echo(f"Analyzing specific repositories: {repos}")
            repo_list = [r.strip() for r in repos.split(",")]
            repositories = analyzer.analyze_specific_repos(
                repo_list, use_nlp=use_nlp, classify_roles=classify_roles
            )

        # Save results
        analyzer.save_results(repositories, output, format_list)

        # Print summary
        click.echo(f"\nAnalysis complete!")
        click.echo(f"Repositories analyzed: {len(repositories)}")
        click.echo(
            f"Total contributors: {sum(len(r.contributors) for r in repositories)}"
        )
        click.echo(f"Results saved to: {output}")

        # Show category breakdown
        categories = {}
        for repo in repositories:
            categories[repo.classification] = categories.get(repo.classification, 0) + 1

        click.echo("\nCategory breakdown:")
        for category, count in sorted(categories.items()):
            click.echo(f"  {category}: {count}")

    except Exception as e:
        click.echo(f"Error during analysis: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("repo_full_name")
@click.option("--output", default="contributor_insights.json", help="Output file")
def contributors(repo_full_name, output):
    """Get detailed insights about contributors to a specific repository."""

    try:
        analyzer = TalentAnalyzer()
        contributors = analyzer.get_contributor_insights(repo_full_name)

        # Save results
        import json

        with open(output, "w") as f:
            json.dump(
                [analyzer._contributor_to_dict(c) for c in contributors],
                f,
                indent=2,
                default=str,
            )

        click.echo(f"Contributor insights saved to: {output}")
        click.echo(f"Total contributors: {len(contributors)}")

        # Show top contributors
        top_contributors = sorted(
            contributors, key=lambda c: c.contributions, reverse=True
        )[:10]
        click.echo("\nTop contributors:")
        for i, contrib in enumerate(top_contributors, 1):
            click.echo(
                f"  {i}. {contrib.login} ({contrib.contributions} contributions)"
            )

    except Exception as e:
        click.echo(f"Error getting contributor insights: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file")
@click.option("--output", default="recruiting_data.json", help="Output file")
def export_recruiting(input_file, output):
    """Convert analysis results to recruiting-optimized format."""

    try:
        import json

        with open(input_file, "r") as f:
            data = json.load(f)

        # Convert back to Repository objects
        from talent_intelligence import Contributor, Repository

        repositories = []
        for repo_data in data:
            contributors = [Contributor(**c) for c in repo_data["contributors"]]
            repo = Repository(
                **{k: v for k, v in repo_data.items() if k != "contributors"}
            )
            repo.contributors = contributors
            repositories.append(repo)

        # Export for recruiting
        analyzer = TalentAnalyzer()
        recruiting_data = analyzer.export_for_recruiting(repositories)

        with open(output, "w") as f:
            json.dump(recruiting_data, f, indent=2, default=str)

        click.echo(f"Recruiting data exported to: {output}")

    except Exception as e:
        click.echo(f"Error exporting recruiting data: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Configuration file path")
def init_config(config):
    """Initialize a configuration file."""

    config_content = """# GitHub Talent Intelligence Platform Configuration

github:
  token: ${GITHUB_TOKEN}  # Will be read from environment variable
  rate_limit_delay: 0.1   # Delay between API calls (seconds)
  max_retries: 3          # Maximum retries for failed requests

analysis:
  use_nlp: true           # Use NLP classification
  classify_roles: true    # Classify contributor roles
  max_commits_per_repo: 100
  max_contributors_per_repo: 50

categories:
  # Add custom keywords for classification
  custom_keywords:
    - "your_keyword"
    - "another_keyword"

output:
  default_formats: ["json", "csv", "recruiting"]
  default_directory: "results"
"""

    try:
        with open(config, "w") as f:
            f.write(config_content)

        click.echo(f"Configuration file created: {config}")
        click.echo("Please edit the file to customize your settings.")

    except Exception as e:
        click.echo(f"Error creating configuration file: {e}", err=True)
        sys.exit(1)


@cli.command()
def setup():
    """Interactive setup for the talent intelligence platform."""

    click.echo("GitHub Talent Intelligence Platform Setup")
    click.echo("=" * 40)

    # Check for GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        click.echo("\nGitHub Token not found in environment variables.")
        click.echo("Please set your GitHub token:")
        click.echo("  export GITHUB_TOKEN=your_token_here")
        click.echo("\nOr create a .env file with:")
        click.echo("  GITHUB_TOKEN=your_token_here")

        if click.confirm("Would you like to create a .env file now?"):
            token = click.prompt("Enter your GitHub token", hide_input=True)
            with open(".env", "w") as f:
                f.write(f"GITHUB_TOKEN={token}\n")
            click.echo("GitHub token saved to .env file")
    else:
        click.echo("✓ GitHub token found")

    # Check for configuration file
    if not os.path.exists("config.yaml"):
        if click.confirm("Would you like to create a configuration file?"):
            init_config.callback("config.yaml")
    else:
        click.echo("✓ Configuration file found")

    # Test connection
    if click.confirm("Would you like to test the GitHub connection?"):
        try:
            analyzer = TalentAnalyzer()
            # Try a simple API call
            response = analyzer.session.get("https://api.github.com/user")
            if response.status_code == 200:
                user_data = response.json()
                click.echo(f"✓ Connected as: {user_data['login']}")
            else:
                click.echo("✗ Failed to connect to GitHub API")
        except Exception as e:
            click.echo(f"✗ Connection test failed: {e}")

    click.echo("\nSetup complete! You can now use the platform:")
    click.echo("  python talent_analyzer.py analyze --org ChainSafe")
    click.echo("  python talent_analyzer.py contributors owner/repo")


if __name__ == "__main__":
    cli()
