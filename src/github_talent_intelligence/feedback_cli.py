import click

from .db import Feedback, ReviewSession, User, get_session, init_db
from .github_oauth import github_device_login
from .gpt_stub import get_chatgpt_suggestion, get_suggestions_for_feedback, update_suggestion_review


@click.group()
def cli():
    """Robot Recruiter Feedback CLI"""
    pass


@cli.command()
def init_db_cmd():
    """Initialize the database tables."""
    init_db()
    click.echo("Database initialized.")


@cli.command()
@click.option("--name", prompt="Name")
@click.option("--email", prompt="Email")
@click.option("--role", prompt="Role (recruiter/reviewer/admin)")
def add_user(name, email, role):
    """Add a new user (reviewer, recruiter, or admin)."""
    db = get_session()
    user = User(name=name, email=email, role=role)
    db.add(user)
    db.commit()
    click.echo(f"User {name} added.")
    db.close()


@cli.command()
@click.option("--user-email", prompt="Your email")
@click.option("--repo", prompt="Repo full name (owner/repo)")
@click.option("--category", prompt="Suggested category")
@click.option("--reason", prompt="Reason for suggestion")
def submit_feedback(user_email, repo, category, reason):
    """Submit feedback for a repo classification."""
    db = get_session()
    user = db.query(User).filter_by(email=user_email).first()
    if not user:
        click.echo("User not found. Please add the user first.")
        db.close()
        return
    feedback = Feedback(
        repo_full_name=repo, suggested_category=category, reason=reason, user_id=user.id
    )
    db.add(feedback)
    db.commit()
    click.echo(f"Feedback submitted for {repo}.")
    db.close()


@cli.command()
def list_feedback():
    """List all feedback entries."""
    db = get_session()
    feedbacks = db.query(Feedback).all()
    for fb in feedbacks:
        user = db.query(User).get(fb.user_id)
        click.echo(
            f"Repo: {fb.repo_full_name}, Category: {fb.suggested_category}, By: {user.email}, Reason: {fb.reason}, Status: {fb.status}"
        )
    db.close()


@cli.command()
@click.option(
    "--client-id", envvar="GITHUB_OAUTH_CLIENT_ID", prompt="GitHub OAuth App Client ID"
)
def login_github(client_id):
    """Authenticate with GitHub via device flow and save token."""
    if client_id == "your-client-id-here":
        client_id = click.prompt("GitHub OAuth App Client ID")
    github_device_login(client_id)


@cli.command()
@click.option('--feedback-id', prompt='Feedback ID', type=int)
@click.option('--temperature', default=0.2, show_default=True, type=float, help='ChatGPT temperature (randomness)')
def generate_chatgpt_suggestion(feedback_id, temperature):
    """Generate a ChatGPT suggestion for a feedback item."""
    db = get_session()
    feedback = db.query(Feedback).get(feedback_id)
    db.close()
    if not feedback:
        click.echo(f"Feedback with ID {feedback_id} not found.")
        return
    prompt = f"Classify the following GitHub repository into one of the categories.\nRepo: {feedback.repo_full_name}\nSuggested category: {feedback.suggested_category}\nReason: {feedback.reason}"
    response = get_chatgpt_suggestion(prompt, feedback_id=feedback_id, temperature=temperature)
    click.echo(f"ChatGPT suggestion: {response}")


if __name__ == "__main__":
    cli()
