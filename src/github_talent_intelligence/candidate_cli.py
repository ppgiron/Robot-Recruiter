"""
CLI for managing candidate database operations.
"""

import click
import json
import os
from pathlib import Path
from candidate_db import DatabaseManager
from config_loader import ConfigLoader


@click.group()
def cli():
    """Robot Recruiter Candidate Database CLI"""
    pass


@cli.command()
@click.option('--database-url', envvar='CANDIDATE_DB_URL', 
              default='postgresql://localhost/robot_recruiter_candidates',
              help='Database connection URL')
def init_db(database_url):
    """Initialize the candidate database tables."""
    try:
        db_manager = DatabaseManager(database_url)
        db_manager.create_tables()
        click.echo("✅ Database tables created successfully!")
    except Exception as e:
        click.echo(f"❌ Error creating database tables: {e}")
        raise click.Abort()


@cli.command()
@click.option('--database-url', envvar='CANDIDATE_DB_URL',
              default='postgresql://localhost/robot_recruiter_candidates',
              help='Database connection URL')
@click.option('--analysis-dir', required=True,
              help='Directory containing analysis results')
@click.option('--session-name', help='Name for this analysis session')
def import_analysis(database_url, analysis_dir, session_name):
    """Import analysis results from CSV/JSON files into the database."""
    analysis_path = Path(analysis_dir)
    
    if not analysis_path.exists():
        click.echo(f"❌ Analysis directory not found: {analysis_dir}")
        raise click.Abort()
    
    # Load analysis results
    analysis_file = analysis_path / 'analysis_results.json'
    if not analysis_file.exists():
        click.echo(f"❌ Analysis results file not found: {analysis_file}")
        raise click.Abort()
    
    try:
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        db_manager = DatabaseManager(database_url)
        
        for repo_data in analysis_data:
            contributors_data = repo_data.get('contributors', [])
            
            # Save to database
            session_id = db_manager.save_repository_analysis(
                repo_data, 
                contributors_data, 
                session_name
            )
            
            click.echo(f"✅ Imported {repo_data.get('full_name')} with {len(contributors_data)} contributors")
        
        click.echo(f"✅ Analysis import completed! Session ID: {session_id}")
        
    except Exception as e:
        click.echo(f"❌ Error importing analysis: {e}")
        raise click.Abort()


@cli.command()
@click.option('--database-url', envvar='CANDIDATE_DB_URL',
              default='postgresql://localhost/robot_recruiter_candidates',
              help='Database connection URL')
@click.option('--limit', default=10, help='Number of candidates to return')
@click.option('--offset', default=0, help='Offset for pagination')
def list_candidates(database_url, limit, offset):
    """List candidate profiles from the database."""
    try:
        db_manager = DatabaseManager(database_url)
        candidates = db_manager.get_candidate_profiles(limit=limit, offset=offset)
        
        if not candidates:
            click.echo("No candidates found in database.")
            return
        
        click.echo(f"\n📋 Found {len(candidates)} candidates:\n")
        
        for candidate in candidates:
            click.echo(f"👤 {candidate.name or candidate.login}")
            click.echo(f"   GitHub: {candidate.login}")
            click.echo(f"   Company: {candidate.company or 'N/A'}")
            click.echo(f"   Location: {candidate.location or 'N/A'}")
            click.echo(f"   Contributions: {candidate.total_contributions}")
            click.echo(f"   Repositories: {candidate.repositories_contributed}")
            click.echo(f"   Followers: {candidate.followers}")
            click.echo(f"   Last Updated: {candidate.last_updated.strftime('%Y-%m-%d %H:%M')}")
            click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error listing candidates: {e}")
        raise click.Abort()


@cli.command()
@click.option('--database-url', envvar='CANDIDATE_DB_URL',
              default='postgresql://localhost/robot_recruiter_candidates',
              help='Database connection URL')
@click.option('--github-id', help='GitHub user ID')
@click.option('--login', help='GitHub username')
def get_candidate(database_url, github_id, login):
    """Get detailed information about a specific candidate."""
    if not github_id and not login:
        click.echo("❌ Please provide either --github-id or --login")
        raise click.Abort()
    
    try:
        db_manager = DatabaseManager(database_url)
        
        if github_id:
            candidate = db_manager.get_candidate_by_github_id(int(github_id))
        else:
            # This would need to be implemented in DatabaseManager
            click.echo("❌ Search by login not yet implemented")
            raise click.Abort()
        
        if not candidate:
            click.echo("❌ Candidate not found")
            return
        
        click.echo(f"\n👤 Candidate Profile: {candidate.name or candidate.login}\n")
        click.echo(f"GitHub ID: {candidate.github_id}")
        click.echo(f"Username: {candidate.login}")
        click.echo(f"Name: {candidate.name or 'N/A'}")
        click.echo(f"Email: {candidate.email or 'N/A'}")
        click.echo(f"Company: {candidate.company or 'N/A'}")
        click.echo(f"Location: {candidate.location or 'N/A'}")
        click.echo(f"Bio: {candidate.bio or 'N/A'}")
        click.echo(f"Blog: {candidate.blog or 'N/A'}")
        click.echo(f"Hireable: {candidate.hireable or 'N/A'}")
        click.echo(f"Public Repos: {candidate.public_repos}")
        click.echo(f"Followers: {candidate.followers}")
        click.echo(f"Following: {candidate.following}")
        click.echo(f"Total Contributions: {candidate.total_contributions}")
        click.echo(f"Repositories Contributed: {candidate.repositories_contributed}")
        click.echo(f"Expertise Score: {candidate.expertise_score or 'N/A'}")
        click.echo(f"Primary Classifications: {candidate.primary_classifications or 'N/A'}")
        click.echo(f"Top Skills: {candidate.top_skills or 'N/A'}")
        click.echo(f"Last Updated: {candidate.last_updated.strftime('%Y-%m-%d %H:%M')}")
        
    except Exception as e:
        click.echo(f"❌ Error getting candidate: {e}")
        raise click.Abort()


@cli.command()
@click.option('--database-url', envvar='CANDIDATE_DB_URL',
              default='postgresql://localhost/robot_recruiter_candidates',
              help='Database connection URL')
@click.option('--location', help='Filter by location')
@click.option('--company', help='Filter by company')
@click.option('--classification', help='Filter by repository classification')
@click.option('--min-contributions', type=int, help='Minimum number of contributions')
@click.option('--min-followers', type=int, help='Minimum number of followers')
def search_candidates(database_url, location, company, classification, min_contributions, min_followers):
    """Search candidates by various criteria."""
    try:
        db_manager = DatabaseManager(database_url)
        candidates = db_manager.search_candidates(
            location=location,
            company=company,
            classification=classification
        )
        
        # Apply additional filters
        if min_contributions:
            candidates = [c for c in candidates if c.total_contributions >= min_contributions]
        
        if min_followers:
            candidates = [c for c in candidates if c.followers >= min_followers]
        
        if not candidates:
            click.echo("No candidates found matching the criteria.")
            return
        
        click.echo(f"\n🔍 Found {len(candidates)} candidates matching criteria:\n")
        
        for candidate in candidates:
            click.echo(f"👤 {candidate.name or candidate.login} (@{candidate.login})")
            click.echo(f"   Company: {candidate.company or 'N/A'}")
            click.echo(f"   Location: {candidate.location or 'N/A'}")
            click.echo(f"   Contributions: {candidate.total_contributions}")
            click.echo(f"   Followers: {candidate.followers}")
            click.echo(f"   Repositories: {candidate.repositories_contributed}")
            click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error searching candidates: {e}")
        raise click.Abort()


@cli.command()
@click.option('--database-url', envvar='CANDIDATE_DB_URL',
              default='postgresql://localhost/robot_recruiter_candidates',
              help='Database connection URL')
def stats(database_url):
    """Show database statistics."""
    try:
        db_manager = DatabaseManager(database_url)
        session = db_manager.get_session()
        
        # Get counts
        repo_count = session.query(db_manager.Repository).count()
        contributor_count = session.query(db_manager.Contributor).count()
        candidate_count = session.query(db_manager.CandidateProfile).count()
        session_count = session.query(db_manager.AnalysisSession).count()
        
        session.close()
        
        click.echo(f"\n📊 Database Statistics:\n")
        click.echo(f"Repositories: {repo_count}")
        click.echo(f"Contributors: {contributor_count}")
        click.echo(f"Candidate Profiles: {candidate_count}")
        click.echo(f"Analysis Sessions: {session_count}")
        
    except Exception as e:
        click.echo(f"❌ Error getting statistics: {e}")
        raise click.Abort()


if __name__ == '__main__':
    cli() 