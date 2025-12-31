"""merge_heads

Revision ID: 69dd43dde1e2
Revises: e4be642f139f
Create Date: 2025-09-30 14:39:11.655204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69dd43dde1e2'
down_revision: Union[str, Sequence[str], None] = 'e4be642f139f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
