"""fix website_category relationships

Revision ID: 8e2fc91e4dde
Revises: 676844ee46a9
Create Date: 2025-05-09 22:56:55.761979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e2fc91e4dde'
down_revision: Union[str, None] = '676844ee46a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
