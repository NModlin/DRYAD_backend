"""merge all heads for prometheus week 1

Revision ID: d725f220e1cf
Revises: 001_create_tool_registry_tables, 001_create_university_tables, 010_enhance_university_system, a5571e77443e
Create Date: 2025-10-29 13:05:22.773001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd725f220e1cf'
down_revision: Union[str, Sequence[str], None] = ('001_create_tool_registry_tables', '001_create_university_tables', '010_enhance_university_system', 'a5571e77443e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
