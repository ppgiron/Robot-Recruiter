"""Create core tables for candidates, repositories, and jobs

Revision ID: create_core_tables
Revises: None
Create Date: 2025-07-04 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'create_core_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create repositories table
    op.create_table(
        'repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('full_name', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('language', sa.String(100)),
        sa.Column('classification', sa.String(100)),
        sa.Column('private', sa.Boolean, default=False),
        sa.Column('html_url', sa.String(500)),
        sa.Column('git_url', sa.String(500)),
        sa.Column('clone_url', sa.String(500)),
        sa.Column('homepage', sa.String(500)),
        sa.Column('size', sa.Integer),
        sa.Column('stargazers_count', sa.Integer),
        sa.Column('watchers_count', sa.Integer),
        sa.Column('forks_count', sa.Integer),
        sa.Column('open_issues_count', sa.Integer),
        sa.Column('license_info', sa.JSON),
        sa.Column('owner_login', sa.String(255)),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('pushed_at', sa.DateTime),
        sa.Column('analysis_date', sa.DateTime, default=sa.func.now()),
    )

    # Create candidate_profiles table
    op.create_table(
        'candidate_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('github_id', sa.Integer, unique=True, nullable=False),
        sa.Column('login', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('email', sa.String(255)),
        sa.Column('bio', sa.Text),
        sa.Column('location', sa.String(255)),
        sa.Column('company', sa.String(255)),
        sa.Column('blog', sa.String(500)),
        sa.Column('twitter_username', sa.String(255)),
        sa.Column('hireable', sa.Boolean),
        sa.Column('public_repos', sa.Integer),
        sa.Column('public_gists', sa.Integer),
        sa.Column('followers', sa.Integer),
        sa.Column('following', sa.Integer),
        sa.Column('total_contributions', sa.Integer, default=0),
        sa.Column('repositories_contributed', sa.Integer, default=0),
        sa.Column('primary_classifications', sa.JSON),
        sa.Column('top_skills', sa.JSON),
        sa.Column('expertise_score', sa.Float),
        sa.Column('last_updated', sa.DateTime, default=sa.func.now()),
    )

    # Create jobs table (minimal schema)
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

def downgrade():
    op.drop_table('jobs')
    op.drop_table('candidate_profiles')
    op.drop_table('repositories') 