"""initial_schema

Revision ID: 163b72f67602
Revises: 
Create Date: 2026-10-23 17:56:07.431467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '163b72f67602'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('firebase_uid', sa.String(length=128), nullable=True),
        sa.Column('auth_provider', sa.String(length=50), nullable=False, server_default='local'),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='salaried'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)

    # 2. financial_profiles
    op.create_table(
        'financial_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('dependents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_income', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('monthly_expenses', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('risk_tolerance', sa.String(length=50), nullable=False, server_default='moderate'),
        sa.Column('emergency_fund_target_months', sa.Integer(), nullable=False, server_default='6'),
        sa.Column('tax_regime_preference', sa.String(length=20), nullable=False, server_default='auto'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_profiles_user_id'), 'financial_profiles', ['user_id'], unique=True)

    # 3. transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='manual'),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_category'), 'transactions', ['category'], unique=False)
    op.create_index(op.f('ix_transactions_date'), 'transactions', ['date'], unique=False)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)

    # 4. liabilities
    op.create_table(
        'liabilities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('principal', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('monthly_emi', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('tenure_months', sa.Integer(), nullable=False),
        sa.Column('remaining_months', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_liabilities_user_id'), 'liabilities', ['user_id'], unique=False)

    # 5. asset_holdings
    op.create_table(
        'asset_holdings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('invested_value', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('current_value', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('expected_return_rate', sa.Numeric(precision=5, scale=2), nullable=False, server_default='6.5'),
        sa.Column('liquidity_days', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asset_holdings_user_id'), 'asset_holdings', ['user_id'], unique=False)

    # 6. financial_goals
    op.create_table(
        'financial_goals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='custom'),
        sa.Column('target_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('current_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_goals_user_id'), 'financial_goals', ['user_id'], unique=False)

    # 7. tax_records
    op.create_table(
        'tax_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('assessment_year', sa.String(length=20), nullable=False),
        sa.Column('gross_income', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('total_deductions', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
        sa.Column('regime', sa.String(length=20), nullable=False),
        sa.Column('calculated_tax', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('calculation_details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tax_records_assessment_year'), 'tax_records', ['assessment_year'], unique=False)
    op.create_index(op.f('ix_tax_records_user_id'), 'tax_records', ['user_id'], unique=False)

    # 8. chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=True),
        sa.Column('tool_invocations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_user_id'), 'chat_messages', ['user_id'], unique=False)

    # 9. scenario_records
    op.create_table(
        'scenario_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('scenario_type', sa.String(length=50), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('result_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenario_records_user_id'), 'scenario_records', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('scenario_records')
    op.drop_table('chat_messages')
    op.drop_table('tax_records')
    op.drop_table('financial_goals')
    op.drop_table('asset_holdings')
    op.drop_table('liabilities')
    op.drop_table('transactions')
    op.drop_table('financial_profiles')
    op.drop_table('users')
