"""merge_heads

Revision ID: da93db43ffab
Revises: b2c3d4e5f6a7, 2025_09_25_multi_client, add_refresh_tokens
Create Date: 2025-09-30 14:25:35.343769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da93db43ffab'
down_revision: Union[str, Sequence[str], None] = ('b2c3d4e5f6a7', '2025_09_25_multi_client', 'add_refresh_tokens')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
