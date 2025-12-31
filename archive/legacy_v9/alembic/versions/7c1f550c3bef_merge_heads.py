"""merge_heads

Revision ID: 7c1f550c3bef
Revises: da93db43ffab
Create Date: 2025-09-30 14:31:16.558597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1f550c3bef'
down_revision: Union[str, Sequence[str], None] = 'da93db43ffab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
