"""Add specs structure to variations

Revision ID: 70a5d605176e
Revises: b93a4d6ff673
Create Date: 2025-05-26 12:30:15.822327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70a5d605176e'
down_revision: Union[str, None] = 'b93a4d6ff673'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
