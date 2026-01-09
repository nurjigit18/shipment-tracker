"""add_warehouse_supplier_tables

Revision ID: 0708f64984ee
Revises: 002_add_organizations
Create Date: 2026-01-06 19:47:22.688270

This migration creates the tables needed for:
1. Warehouses - destination locations
2. Suppliers - supplier companies
3. ProductModels - product model names (shirt, pants, etc.)
4. ProductColors - product colors (red, blue, etc.)
5. UserSuppliers - many-to-many relationship between users and suppliers
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0708f64984ee'
down_revision: Union[str, None] = '002_add_organizations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create warehouses table
    op.create_table(
        'warehouses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_warehouses_id', 'warehouses', ['id'])
    op.create_index('ix_warehouses_organization_id', 'warehouses', ['organization_id'])

    # Create suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_suppliers_id', 'suppliers', ['id'])
    op.create_index('ix_suppliers_organization_id', 'suppliers', ['organization_id'])

    # Create product_models table
    op.create_table(
        'product_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_product_models_id', 'product_models', ['id'])
    op.create_index('ix_product_models_organization_id', 'product_models', ['organization_id'])

    # Create product_colors table
    op.create_table(
        'product_colors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_product_colors_id', 'product_colors', ['id'])
    op.create_index('ix_product_colors_organization_id', 'product_colors', ['organization_id'])

    # Create user_suppliers many-to-many table
    op.create_table(
        'user_suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'supplier_id', name='uq_user_supplier')
    )
    op.create_index('ix_user_suppliers_id', 'user_suppliers', ['id'])
    op.create_index('ix_user_suppliers_user_id', 'user_suppliers', ['user_id'])
    op.create_index('ix_user_suppliers_supplier_id', 'user_suppliers', ['supplier_id'])

    # Insert some default warehouses for testing
    op.execute("""
        INSERT INTO warehouses (name, is_active, organization_id, created_at, updated_at)
        SELECT 'Казань', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Краснодар', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Электросталь', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Коледино', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Тула', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Невинномысск', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Рязань', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Новосибирск', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Алматы', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
        UNION ALL
        SELECT 'Котовск', true, id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM organizations WHERE name = 'Default Company'
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_user_suppliers_supplier_id', table_name='user_suppliers')
    op.drop_index('ix_user_suppliers_user_id', table_name='user_suppliers')
    op.drop_index('ix_user_suppliers_id', table_name='user_suppliers')
    op.drop_table('user_suppliers')

    op.drop_index('ix_product_colors_organization_id', table_name='product_colors')
    op.drop_index('ix_product_colors_id', table_name='product_colors')
    op.drop_table('product_colors')

    op.drop_index('ix_product_models_organization_id', table_name='product_models')
    op.drop_index('ix_product_models_id', table_name='product_models')
    op.drop_table('product_models')

    op.drop_index('ix_suppliers_organization_id', table_name='suppliers')
    op.drop_index('ix_suppliers_id', table_name='suppliers')
    op.drop_table('suppliers')

    op.drop_index('ix_warehouses_organization_id', table_name='warehouses')
    op.drop_index('ix_warehouses_id', table_name='warehouses')
    op.drop_table('warehouses')
