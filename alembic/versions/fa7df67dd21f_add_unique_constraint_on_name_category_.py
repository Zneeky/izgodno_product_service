"""Add unique constraint on (name, category_id, brand)

Revision ID: fa7df67dd21f
Revises: 8e91c3c23706
Create Date: 2025-06-28 23:33:20.849249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa7df67dd21f'
down_revision: Union[str, None] = '8e91c3c23706'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('uq_product_name_category_brand', 'products', ['name', 'category_id', 'brand'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uq_product_name_category_brand', 'products', type_='unique')
    # ### end Alembic commands ###
