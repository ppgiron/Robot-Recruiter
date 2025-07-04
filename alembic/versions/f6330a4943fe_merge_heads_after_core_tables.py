"""Merge heads after core tables

Revision ID: f6330a4943fe
Revises: e95e4c1caf17
Create Date: 2025-07-03 23:52:58.017018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6330a4943fe'
down_revision: Union[str, Sequence[str], None] = 'e95e4c1caf17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
