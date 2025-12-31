"""merge_oauth2_and_analytics

Revision ID: 0b2f849dc961
Revises: 7df615c12ca9, add_analytics_tables, add_oauth2_user_model
Create Date: 2025-08-25 18:22:58.919052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b2f849dc961'
down_revision: Union[str, Sequence[str], None] = ('7df615c12ca9', 'add_analytics_tables', 'add_oauth2_user_model')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
