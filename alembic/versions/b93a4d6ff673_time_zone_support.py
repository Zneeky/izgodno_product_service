"""time zone support

Revision ID: b93a4d6ff673
Revises: 8e2fc91e4dde
Create Date: 2025-05-10 15:30:30.435882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b93a4d6ff673'
down_revision: Union[str, None] = '8e2fc91e4dde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
