"""merge_radar_and_dryad_heads

Revision ID: 5138ffd0568f
Revises: 001_add_dryad_tables, 203c7ac46675, radar_integration_001
Create Date: 2025-10-03 17:28:20.336463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5138ffd0568f'
down_revision: Union[str, Sequence[str], None] = ('001_add_dryad_tables', '203c7ac46675', 'radar_integration_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
