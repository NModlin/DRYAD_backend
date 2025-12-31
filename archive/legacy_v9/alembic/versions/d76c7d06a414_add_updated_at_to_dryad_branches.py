"""add_updated_at_to_dryad_branches

Revision ID: d76c7d06a414
Revises: 5138ffd0568f
Create Date: 2025-10-06 16:54:43.287679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd76c7d06a414'
down_revision: Union[str, Sequence[str], None] = '5138ffd0568f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add updated_at column to dryad_branches table."""
    # Add updated_at column with default value
    op.add_column('dryad_branches',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('(CURRENT_TIMESTAMP)'))
    )


def downgrade() -> None:
    """Remove updated_at column from dryad_branches table."""
    op.drop_column('dryad_branches', 'updated_at')
