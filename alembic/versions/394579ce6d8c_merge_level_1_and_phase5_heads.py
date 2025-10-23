"""merge_level_1_and_phase5_heads

Revision ID: 394579ce6d8c
Revises: 2025_01_11_create_tool_executions_table, 632791431de1
Create Date: 2025-10-11 19:10:53.635140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '394579ce6d8c'
down_revision: Union[str, Sequence[str], None] = ('2025_01_11_create_tool_executions_table', '632791431de1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
