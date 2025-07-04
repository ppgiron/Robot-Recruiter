"""Add continuous learning feedback tables

Revision ID: continuous_learning_feedback
Revises: 0942d2b782e2
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'continuous_learning_feedback'
down_revision = '0942d2b782e2'
branch_labels = None
depends_on = None


def upgrade():
    # Create feedback_data table
    op.create_table('feedback_data',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=True),
        sa.Column('candidate_id', sa.String(36), nullable=True),
        sa.Column('client_id', sa.String(36), nullable=True),
        sa.Column('placement_id', sa.String(36), nullable=True),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('processed', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes
    op.create_index('idx_feedback_type', 'feedback_data', ['feedback_type'])
    op.create_index('idx_feedback_source', 'feedback_data', ['source'])
    op.create_index('idx_feedback_timestamp', 'feedback_data', ['timestamp'])
    op.create_index('idx_feedback_processed', 'feedback_data', ['processed'])
    op.create_index('idx_feedback_session', 'feedback_data', ['session_id'])
    op.create_index('idx_feedback_candidate', 'feedback_data', ['candidate_id'])
    
    # Create model_performance table
    op.create_table('model_performance',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('accuracy', sa.Float, nullable=False),
        sa.Column('precision', sa.Float, nullable=False),
        sa.Column('recall', sa.Float, nullable=False),
        sa.Column('f1_score', sa.Float, nullable=False),
        sa.Column('training_samples', sa.Integer, nullable=False),
        sa.Column('test_samples', sa.Integer, nullable=False),
        sa.Column('performance_trend', sa.JSON, nullable=True),
        sa.Column('last_updated', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Create indexes for model_performance
    op.create_index('idx_model_name', 'model_performance', ['model_name'])
    op.create_index('idx_model_version', 'model_performance', ['version'])
    op.create_index('idx_model_last_updated', 'model_performance', ['last_updated'])
    
    # Create learning_signals table
    op.create_table('learning_signals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('feature_name', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('importance_score', sa.Float, nullable=False),
        sa.Column('direction', sa.String(20), nullable=False),  # increase, decrease, maintain
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('sample_size', sa.Integer, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Create indexes for learning_signals
    op.create_index('idx_signal_feature', 'learning_signals', ['feature_name'])
    op.create_index('idx_signal_model', 'learning_signals', ['model_name'])
    op.create_index('idx_signal_timestamp', 'learning_signals', ['timestamp'])
    
    # Create placement_outcomes table for tracking success
    op.create_table('placement_outcomes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('placement_id', sa.String(36), nullable=False),
        sa.Column('candidate_id', sa.String(36), nullable=False),
        sa.Column('client_id', sa.String(36), nullable=False),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('satisfaction_score', sa.Float, nullable=True),
        sa.Column('duration_days', sa.Integer, nullable=True),
        sa.Column('salary_achieved', sa.Float, nullable=True),
        sa.Column('feedback_notes', sa.Text, nullable=True),
        sa.Column('outcome_date', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Create indexes for placement_outcomes
    op.create_index('idx_placement_id', 'placement_outcomes', ['placement_id'])
    op.create_index('idx_placement_success', 'placement_outcomes', ['success'])
    op.create_index('idx_placement_outcome_date', 'placement_outcomes', ['outcome_date'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('placement_outcomes')
    op.drop_table('learning_signals')
    op.drop_table('model_performance')
    op.drop_table('feedback_data') 