"""add website_categories join table

Revision ID: 676844ee46a9
Revises: eca2e54cbe0a
Create Date: 2025-05-09 22:53:29.669521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '676844ee46a9'
down_revision: Union[str, None] = 'eca2e54cbe0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
