"""add_shipment_type_column

Revision ID: 9fcd469291f7
Revises: a3ef7d6a2cf0
Create Date: 2026-01-10 15:56:23.333293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fcd469291f7'
down_revision: Union[str, None] = 'a3ef7d6a2cf0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add shipment_type column with default value 'BAGS'
    op.add_column('shipments', sa.Column('shipment_type', sa.String(length=20), nullable=False, server_default='BAGS'))


def downgrade() -> None:
    # Remove shipment_type column
    op.drop_column('shipments', 'shipment_type')
