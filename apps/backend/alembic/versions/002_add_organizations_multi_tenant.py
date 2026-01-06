"""Add organizations table and multi-tenant support

Revision ID: 002_add_organizations
Revises: 0b6739e23b29
Create Date: 2026-01-04

This migration adds multi-tenant organization support:
1. Creates organizations table
2. Inserts "Default Company" for existing data
3. Adds organization_id columns to users, shipments, user_logs, shipment_status_history
4. Migrates existing data to Default Company
5. Adds foreign keys and indexes
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_organizations'
down_revision = '0b6739e23b29'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_organizations_name', 'organizations', ['name'])
    op.create_unique_constraint('uq_organizations_name', 'organizations', ['name'])

    # 2. Insert default organization for existing data
    op.execute("""
        INSERT INTO organizations (name, created_at, updated_at)
        VALUES ('Default Company', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    # 3. Add organization_id columns (nullable initially)
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.add_column('shipments', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.add_column('shipment_status_history', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.add_column('user_logs', sa.Column('organization_id', sa.Integer(), nullable=True))

    # 4. Migrate existing data to Default Company
    op.execute("""
        UPDATE users
        SET organization_id = (SELECT id FROM organizations WHERE name = 'Default Company')
    """)

    op.execute("""
        UPDATE shipments
        SET organization_id = (SELECT id FROM organizations WHERE name = 'Default Company')
    """)

    op.execute("""
        UPDATE shipment_status_history
        SET organization_id = (
            SELECT organization_id
            FROM shipments
            WHERE shipments.id = shipment_status_history.shipment_id
        )
    """)

    op.execute("""
        UPDATE user_logs
        SET organization_id = (
            SELECT organization_id
            FROM users
            WHERE users.id = user_logs.user_id
        )
    """)

    # 5. Make organization_id NOT NULL for core tables
    op.alter_column('users', 'organization_id', nullable=False)
    op.alter_column('shipments', 'organization_id', nullable=False)
    # Note: shipment_status_history and user_logs keep nullable for analytics

    # 6. Create foreign key constraints
    op.create_foreign_key(
        'fk_users_organization',
        'users',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_shipments_organization',
        'shipments',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_shipment_status_history_organization',
        'shipment_status_history',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_user_logs_organization',
        'user_logs',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # 7. Create indexes for performance
    op.create_index('idx_users_organization_id', 'users', ['organization_id'])
    op.create_index('idx_shipments_organization_id', 'shipments', ['organization_id'])
    op.create_index('idx_shipment_status_history_organization_id', 'shipment_status_history', ['organization_id'])
    op.create_index('idx_user_logs_organization_id', 'user_logs', ['organization_id'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_user_logs_organization_id', table_name='user_logs')
    op.drop_index('idx_shipment_status_history_organization_id', table_name='shipment_status_history')
    op.drop_index('idx_shipments_organization_id', table_name='shipments')
    op.drop_index('idx_users_organization_id', table_name='users')

    # Remove foreign keys
    op.drop_constraint('fk_user_logs_organization', 'user_logs', type_='foreignkey')
    op.drop_constraint('fk_shipment_status_history_organization', 'shipment_status_history', type_='foreignkey')
    op.drop_constraint('fk_shipments_organization', 'shipments', type_='foreignkey')
    op.drop_constraint('fk_users_organization', 'users', type_='foreignkey')

    # Remove columns
    op.drop_column('user_logs', 'organization_id')
    op.drop_column('shipment_status_history', 'organization_id')
    op.drop_column('shipments', 'organization_id')
    op.drop_column('users', 'organization_id')

    # Drop organizations table
    op.drop_index('idx_organizations_name', table_name='organizations')
    op.drop_table('organizations')
