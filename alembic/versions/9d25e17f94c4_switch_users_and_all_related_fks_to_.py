"""Switch users and all related FKs to UUID primary key

Revision ID: 9d25e17f94c4
Revises: continuous_learning_feedback
Create Date: 2025-07-01 21:56:18.373423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = '9d25e17f94c4'
down_revision: Union[str, Sequence[str], None] = 'continuous_learning_feedback'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop dependent tables first due to FK constraints
    op.drop_table('voice_enhanced_suggestions')
    op.drop_table('transcriptions')
    op.drop_table('review_assignments')
    op.drop_table('chatgpt_interactions')
    op.drop_table('voice_notes')
    op.drop_table('feedback')
    op.drop_table('review_sessions')
    op.drop_table('users')

    # Recreate users table with UUID PK
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=200), unique=True, nullable=False),
        sa.Column('role', sa.String(length=50), default='recruiter'),
        sa.Column('reviewer_level', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )

    # Recreate review_sessions table
    op.create_table(
        'review_sessions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(length=50), default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_completion_date', sa.DateTime(timezone=True), nullable=True),
    )

    # Recreate feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('repo_full_name', sa.String(length=200), nullable=False),
        sa.Column('suggested_category', sa.String(length=100), nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('review_session_id', sa.Integer, sa.ForeignKey('review_sessions.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=50), default='pending'),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # Recreate review_assignments table
    op.create_table(
        'review_assignments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('feedback_id', sa.Integer, sa.ForeignKey('feedback.id'), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('review_session_id', sa.Integer, sa.ForeignKey('review_sessions.id'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.String(length=20), default='normal'),
        sa.Column('status', sa.String(length=50), default='assigned'),
        sa.Column('notes', sa.Text, nullable=True),
    )

    # Recreate voice_notes table
    op.create_table(
        'voice_notes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('feedback_id', sa.Integer, sa.ForeignKey('feedback.id'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('audio_file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('audio_format', sa.String(length=20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('storage_type', sa.String(length=20), default='local'),
        sa.Column('cloud_url', sa.String(length=500), nullable=True),
    )

    # Recreate chatgpt_interactions table
    op.create_table(
        'chatgpt_interactions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('prompt', sa.Text, nullable=False),
        sa.Column('response', sa.Text, nullable=True),
        sa.Column('model', sa.String(length=100), default='gpt-3.5-turbo'),
        sa.Column('temperature', sa.Integer, default=2),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('feedback_id', sa.Integer, sa.ForeignKey('feedback.id'), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('review_status', sa.String(length=50), default='pending'),
        sa.Column('review_comment', sa.Text, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop all affected tables
    op.drop_table('chatgpt_interactions')
    op.drop_table('voice_notes')
    op.drop_table('feedback')
    op.drop_table('review_assignments')
    op.drop_table('review_sessions')
    op.drop_table('users')
