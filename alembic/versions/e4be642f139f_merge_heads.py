"""merge_heads

Revision ID: e4be642f139f
Revises: 7c1f550c3bef
Create Date: 2025-09-30 14:38:04.945849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4be642f139f'
down_revision: Union[str, Sequence[str], None] = '7c1f550c3bef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
