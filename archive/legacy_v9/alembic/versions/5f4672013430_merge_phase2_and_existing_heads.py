"""merge_phase2_and_existing_heads

Revision ID: 5f4672013430
Revises: 006_progression_paths, 394579ce6d8c
Create Date: 2025-10-23 00:09:27.742088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f4672013430'
down_revision: Union[str, Sequence[str], None] = ('006_progression_paths', '394579ce6d8c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
