"""add_fulfillment_id_and_owner_role

Revision ID: 2abad51cd95f
Revises: 74931d7a0a65
Create Date: 2026-01-12 18:11:11.742415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2abad51cd95f'
down_revision: Union[str, None] = '74931d7a0a65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add fulfillment_id column to users table
    op.add_column('users', sa.Column('fulfillment_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_fulfillment_id'), 'users', ['fulfillment_id'], unique=False)
    op.create_foreign_key('fk_users_fulfillment_id', 'users', 'fulfillments', ['fulfillment_id'], ['id'])

    # Insert "owner" role into roles table
    op.execute("INSERT INTO roles (name) VALUES ('owner') ON CONFLICT (name) DO NOTHING")


def downgrade() -> None:
    # Remove "owner" role
    op.execute("DELETE FROM roles WHERE name = 'owner'")

    # Remove fulfillment_id column from users table
    op.drop_constraint('fk_users_fulfillment_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_fulfillment_id'), table_name='users')
    op.drop_column('users', 'fulfillment_id')
