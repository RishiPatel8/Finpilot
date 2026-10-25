"""add_recurring_transactions_table

Revision ID: c92e742810a1
Revises: b84f3189e472
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c92e742810a1'
down_revision: Union[str, Sequence[str], None] = 'b84f3189e472'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'recurring_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('bank_account_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('merchant', sa.String(length=255), nullable=True),
        sa.Column('transaction_type', sa.String(length=20), nullable=False, server_default='expense'),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('frequency', sa.String(length=30), nullable=False, server_default='monthly'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='detected'),
        sa.Column('confidence', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('detection_source', sa.String(length=50), nullable=False, server_default='intelligence_engine'),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('next_expected_date', sa.Date(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('last_occurrence_date', sa.Date(), nullable=True),
        sa.Column('occurrence_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('user_confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recurring_transactions_user_id'), 'recurring_transactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_recurring_transactions_status'), 'recurring_transactions', ['status'], unique=False)
    op.create_index(op.f('ix_recurring_transactions_category'), 'recurring_transactions', ['category'], unique=False)
    op.create_index(op.f('ix_recurring_transactions_next_expected_date'), 'recurring_transactions', ['next_expected_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_recurring_transactions_next_expected_date'), table_name='recurring_transactions')
    op.drop_index(op.f('ix_recurring_transactions_category'), table_name='recurring_transactions')
    op.drop_index(op.f('ix_recurring_transactions_status'), table_name='recurring_transactions')
    op.drop_index(op.f('ix_recurring_transactions_user_id'), table_name='recurring_transactions')
    op.drop_table('recurring_transactions')
