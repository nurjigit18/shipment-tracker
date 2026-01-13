"""make_organization_id_nullable

Revision ID: 370dac5c6bff
Revises: 2abad51cd95f
Create Date: 2026-01-12 23:20:06.990792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '370dac5c6bff'
down_revision: Union[str, None] = '2abad51cd95f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make organization_id nullable so owners can remove users from organizations
    op.alter_column('users', 'organization_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade() -> None:
    # Revert organization_id back to NOT NULL
    # First, update any NULL values to a default organization (assumes org with id=1 exists)
    op.execute("UPDATE users SET organization_id = 1 WHERE organization_id IS NULL")

    op.alter_column('users', 'organization_id',
                    existing_type=sa.Integer(),
                    nullable=False)
