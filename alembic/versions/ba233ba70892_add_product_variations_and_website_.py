"""Add product_variations and website_categories

Revision ID: ba233ba70892
Revises: 3569a91e047a
Create Date: 2025-05-26 13:30:04.903733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba233ba70892'
down_revision: Union[str, None] = '3569a91e047a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
