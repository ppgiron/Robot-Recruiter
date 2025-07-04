"""
Merge continuous learning feedback

Revision ID: e95e4c1caf17
Revises: 3ca67c58cd8c
Create Date: 2025-07-03 18:46:22.247487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e95e4c1caf17'
down_revision = '3ca67c58cd8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
