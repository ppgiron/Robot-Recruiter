"""
Review Workflow CLI Commands
"""

import click
from datetime import datetime, timedelta
from typing import Optional

from .db import get_session, User, Feedback, ReviewSession, ReviewAssignment
from .review_workflow import ReviewWorkflowManager


@click.group()
def review():
    """Review workflow management commands."""
    pass


@review.command()
@click.option('--name', prompt='Review session name', help='Name for the review session')
@click.option('--reviewer-email', prompt='Reviewer email', help='Email of the reviewer')
@click.option('--description', help='Optional description')
@click.option('--target-days', type=int, help='Target completion in days from now')
def create_session(name, reviewer_email, description, target_days):
    """Create a new review session."""
    db = get_session()
    try:
        # Find reviewer
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            click.echo(f"❌ User with email {reviewer_email} not found")
            return
        
        # Calculate target date
        target_date = None
        if target_days:
            target_date = datetime.now() + timedelta(days=target_days)
        
        # Create session
        workflow = ReviewWorkflowManager()
        session = workflow.create_review_session(
            name=name,
            reviewer_id=reviewer.id,
            description=description,
            target_completion_date=target_date
        )
        
        click.echo(f"✅ Created review session: {session.name} (ID: {session.id})")
        click.echo(f"   Reviewer: {reviewer.name} ({reviewer.email})")
        if target_date:
            click.echo(f"   Target completion: {target_date.strftime('%Y-%m-%d')}")
        
    finally:
        db.close()


@review.command()
@click.option('--feedback-id', prompt='Feedback ID', type=int, help='ID of feedback to assign')
@click.option('--reviewer-email', prompt='Reviewer email', help='Email of the reviewer')
@click.option('--session-id', type=int, help='Optional review session ID')
@click.option('--priority', type=click.Choice(['low', 'normal', 'high', 'urgent']), default='normal', help='Assignment priority')
@click.option('--due-days', type=int, help='Due date in days from now')
@click.option('--notes', help='Assignment notes')
def assign_feedback(feedback_id, reviewer_email, session_id, priority, due_days, notes):
    """Assign feedback to a reviewer."""
    db = get_session()
    try:
        # Find reviewer
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            click.echo(f"❌ User with email {reviewer_email} not found")
            return
        
        # Calculate due date
        due_date = None
        if due_days:
            due_date = datetime.now() + timedelta(days=due_days)
        
        # Assign feedback
        workflow = ReviewWorkflowManager()
        assignment = workflow.assign_feedback_to_reviewer(
            feedback_id=feedback_id,
            reviewer_id=reviewer.id,
            review_session_id=session_id,
            priority=priority,
            due_date=due_date,
            notes=notes
        )
        
        click.echo(f"✅ Assigned feedback {feedback_id} to {reviewer.name}")
        click.echo(f"   Assignment ID: {assignment.id}")
        click.echo(f"   Priority: {assignment.priority}")
        if due_date:
            click.echo(f"   Due date: {due_date.strftime('%Y-%m-%d %H:%M')}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@review.command()
@click.option('--reviewer-email', prompt='Reviewer email', help='Email of the reviewer')
@click.option('--status', type=click.Choice(['assigned', 'in_review', 'completed', 'overdue']), help='Filter by status')
def list_assignments(reviewer_email, status):
    """List assignments for a reviewer."""
    db = get_session()
    try:
        # Find reviewer
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            click.echo(f"❌ User with email {reviewer_email} not found")
            return
        
        # Get assignments
        workflow = ReviewWorkflowManager()
        assignments = workflow.get_reviewer_assignments(
            reviewer_id=reviewer.id,
            status=status
        )
        
        if not assignments:
            click.echo(f"📭 No assignments found for {reviewer.name}")
            return
        
        click.echo(f"📋 Assignments for {reviewer.name}:")
        click.echo("=" * 80)
        
        for assignment in assignments:
            status_icon = {
                'assigned': '📋',
                'in_review': '🔍',
                'completed': '✅',
                'overdue': '⏰'
            }.get(assignment['status'], '❓')
            
            overdue_indicator = " (OVERDUE)" if assignment['is_overdue'] else ""
            voice_notes_indicator = f" 🎤{assignment['voice_notes_count']}" if assignment['voice_notes_count'] > 0 else ""
            
            click.echo(f"{status_icon} {assignment['assignment_id']}: {assignment['repo_full_name']}")
            click.echo(f"   Category: {assignment['suggested_category']}")
            click.echo(f"   Status: {assignment['status']}{overdue_indicator}")
            click.echo(f"   Priority: {assignment['priority']}{voice_notes_indicator}")
            click.echo(f"   Assigned: {assignment['assigned_at'][:10]}")
            if assignment['due_date']:
                click.echo(f"   Due: {assignment['due_date'][:10]}")
            if assignment['notes']:
                click.echo(f"   Notes: {assignment['notes']}")
            click.echo()
        
    finally:
        db.close()


@review.command()
@click.option('--assignment-id', prompt='Assignment ID', type=int, help='ID of assignment to update')
@click.option('--status', prompt='New status', type=click.Choice(['assigned', 'in_review', 'completed']), help='New status')
@click.option('--notes', help='Update notes')
def update_assignment(assignment_id, status, notes):
    """Update assignment status."""
    try:
        workflow = ReviewWorkflowManager()
        assignment = workflow.update_assignment_status(
            assignment_id=assignment_id,
            status=status,
            notes=notes
        )
        
        click.echo(f"✅ Updated assignment {assignment_id}")
        click.echo(f"   New status: {assignment.status}")
        if notes:
            click.echo(f"   Notes: {assignment.notes}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@review.command()
@click.option('--feedback-id', prompt='Feedback ID', type=int, help='ID of feedback to review')
@click.option('--reviewer-email', prompt='Reviewer email', help='Email of the reviewer')
@click.option('--decision', prompt='Review decision', type=click.Choice(['approved', 'rejected', 'needs_revision']), help='Review decision')
@click.option('--notes', help='Review notes')
@click.option('--voice-note-id', type=int, help='Optional voice note ID to link')
def submit_review(feedback_id, reviewer_email, decision, notes, voice_note_id):
    """Submit a review decision."""
    db = get_session()
    try:
        # Find reviewer
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            click.echo(f"❌ User with email {reviewer_email} not found")
            return
        
        # Submit review
        workflow = ReviewWorkflowManager()
        feedback = workflow.submit_review(
            feedback_id=feedback_id,
            reviewer_id=reviewer.id,
            review_decision=decision,
            review_notes=notes,
            voice_note_id=voice_note_id
        )
        
        decision_icon = {
            'approved': '✅',
            'rejected': '❌',
            'needs_revision': '🔄'
        }.get(decision, '❓')
        
        click.echo(f"{decision_icon} Review submitted for feedback {feedback_id}")
        click.echo(f"   Decision: {feedback.status}")
        click.echo(f"   Reviewer: {reviewer.name}")
        if notes:
            click.echo(f"   Notes: {feedback.review_notes}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()


@review.command()
@click.option('--session-id', prompt='Session ID', type=int, help='ID of review session')
def session_summary(session_id):
    """Get summary statistics for a review session."""
    try:
        workflow = ReviewWorkflowManager()
        summary = workflow.get_review_session_summary(session_id)
        
        click.echo(f"📊 Review Session Summary: {summary['session_name']}")
        click.echo("=" * 50)
        click.echo(f"Session ID: {summary['session_id']}")
        click.echo(f"Status: {summary['status']}")
        click.echo(f"Created: {summary['created_at'][:10]}")
        if summary['target_completion_date']:
            click.echo(f"Target completion: {summary['target_completion_date'][:10]}")
        
        click.echo("\n📈 Statistics:")
        stats = summary['statistics']
        click.echo(f"   Total assignments: {stats['total_assignments']}")
        click.echo(f"   Completed: {stats['completed']}")
        click.echo(f"   In review: {stats['in_review']}")
        click.echo(f"   Overdue: {stats['overdue']}")
        click.echo(f"   Completion rate: {stats['completion_rate']:.1f}%")
        
        if summary['feedback_statuses']:
            click.echo("\n📋 Feedback Status Breakdown:")
            for status, count in summary['feedback_statuses'].items():
                click.echo(f"   {status}: {count}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@review.command()
@click.option('--reviewer-email', prompt='Reviewer email', help='Email of the reviewer')
@click.option('--days', type=int, default=30, help='Number of days to analyze')
def performance_stats(reviewer_email, days):
    """Get performance statistics for a reviewer."""
    db = get_session()
    try:
        # Find reviewer
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            click.echo(f"❌ User with email {reviewer_email} not found")
            return
        
        # Get performance stats
        workflow = ReviewWorkflowManager()
        stats = workflow.get_reviewer_performance_stats(reviewer.id, days)
        
        click.echo(f"📊 Performance Stats for {reviewer.name}")
        click.echo("=" * 40)
        click.echo(f"Period: Last {stats['period_days']} days")
        click.echo(f"Total completed: {stats['total_completed']}")
        click.echo(f"Avg completion time: {stats['avg_completion_time_hours']} hours")
        
        if stats['decision_breakdown']:
            click.echo("\n📋 Decision Breakdown:")
            for decision, count in stats['decision_breakdown'].items():
                click.echo(f"   {decision}: {count}")
        
    finally:
        db.close()


@review.command()
@click.option('--reviewer-email', prompt='Reviewer email', help='Email of the reviewer')
@click.option('--max-assignments', type=int, default=10, help='Maximum assignments to auto-assign')
def auto_assign(reviewer_email, max_assignments):
    """Automatically assign pending feedback to a reviewer."""
    db = get_session()
    try:
        # Find reviewer
        reviewer = db.query(User).filter_by(email=reviewer_email).first()
        if not reviewer:
            click.echo(f"❌ User with email {reviewer_email} not found")
            return
        
        # Auto-assign
        workflow = ReviewWorkflowManager()
        assignments = workflow.auto_assign_pending_feedback(
            reviewer_id=reviewer.id,
            max_assignments=max_assignments
        )
        
        if not assignments:
            click.echo(f"📭 No pending feedback available for {reviewer.name}")
            return
        
        click.echo(f"✅ Auto-assigned {len(assignments)} feedback items to {reviewer.name}")
        for assignment in assignments:
            click.echo(f"   Feedback {assignment.feedback_id}: {assignment.feedback.repo_full_name}")
        
    finally:
        db.close()


if __name__ == '__main__':
    review() 