"""add vector tables for semantic search

Revision ID: 3ca67c58cd8c
Revises: 9d25e17f94c4
Create Date: 2025-07-03 00:36:27.377735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '3ca67c58cd8c'
down_revision: Union[str, Sequence[str], None] = '9d25e17f94c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VECTOR_DIM = 384

def upgrade() -> None:
    """Upgrade schema."""
    # Ensure pgvector extension is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Candidate Embeddings
    op.execute("""
        CREATE TABLE candidate_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
            embedding vector(384) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            meta JSON
        );
    """)
    op.execute("CREATE INDEX ix_candidate_embedding ON candidate_embeddings USING ivfflat (embedding vector_cosine_ops);")

    # Job Embeddings
    op.execute("""
        CREATE TABLE job_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
            embedding vector(384) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            meta JSON
        );
    """)
    op.execute("CREATE INDEX ix_job_embedding ON job_embeddings USING ivfflat (embedding vector_cosine_ops);")

    # Code Embeddings
    op.execute("""
        CREATE TABLE code_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            repo_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
            embedding vector(384) NOT NULL,
            created_at TIMESTAMP DEFAULT now(),
            meta JSON
        );
    """)
    op.execute("CREATE INDEX ix_code_embedding ON code_embeddings USING ivfflat (embedding vector_cosine_ops);")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_code_embedding', table_name='code_embeddings')
    op.drop_table('code_embeddings')
    op.drop_index('ix_job_embedding', table_name='job_embeddings')
    op.drop_table('job_embeddings')
    op.drop_index('ix_candidate_embedding', table_name='candidate_embeddings')
    op.drop_table('candidate_embeddings')
    op.execute("DROP EXTENSION IF EXISTS vector;")
