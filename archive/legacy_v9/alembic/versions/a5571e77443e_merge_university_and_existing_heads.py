"""merge_university_and_existing_heads

Revision ID: a5571e77443e
Revises: 009_add_competition_system, 5f4672013430
Create Date: 2025-10-23 00:51:13.034618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5571e77443e'
down_revision: Union[str, Sequence[str], None] = ('009_add_competition_system', '5f4672013430')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
