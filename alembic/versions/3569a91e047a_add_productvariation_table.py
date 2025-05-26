"""Add ProductVariation table

Revision ID: 3569a91e047a
Revises: 70a5d605176e
Create Date: 2025-05-26 13:18:06.750970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3569a91e047a'
down_revision: Union[str, None] = '70a5d605176e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
