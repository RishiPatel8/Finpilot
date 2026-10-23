"""add_bank_connectivity_tables

Revision ID: b84f3189e472
Revises: 163b72f67602
Create Date: 2026-10-23 18:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'b84f3189e472'
down_revision: Union[str, Sequence[str], None] = '163b72f67602'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. bank_consents
    op.create_table(
        'bank_consents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('consent_handle', sa.String(length=128), nullable=False),
        sa.Column('consent_id', sa.String(length=128), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('fip_ids', sa.JSON(), nullable=True),
        sa.Column('fi_types', sa.JSON(), nullable=False),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_to', sa.DateTime(), nullable=False),
        sa.Column('fetch_frequency', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_consents_user_id'), 'bank_consents', ['user_id'], unique=False)
    op.create_index(op.f('ix_bank_consents_consent_handle'), 'bank_consents', ['consent_handle'], unique=True)
    op.create_index(op.f('ix_bank_consents_consent_id'), 'bank_consents', ['consent_id'], unique=True)

    # 2. bank_accounts
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('consent_id', sa.String(length=36), nullable=True),
        sa.Column('institution_name', sa.String(length=100), nullable=False),
        sa.Column('account_number_masked', sa.String(length=50), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('ifsc_code', sa.String(length=20), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('current_balance', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('balance_type', sa.String(length=30), nullable=False),
        sa.Column('balance_timestamp', sa.DateTime(), nullable=False),
        sa.Column('sync_status', sa.String(length=30), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['consent_id'], ['bank_consents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_accounts_user_id'), 'bank_accounts', ['user_id'], unique=False)
    op.create_index(op.f('ix_bank_accounts_consent_id'), 'bank_accounts', ['consent_id'], unique=False)

    # 3. bank_sync_logs
    op.create_table(
        'bank_sync_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('sync_status', sa.String(length=20), nullable=False),
        sa.Column('records_synced', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_sync_logs_user_id'), 'bank_sync_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_bank_sync_logs_account_id'), 'bank_sync_logs', ['account_id'], unique=False)

    # 4. transactions alterations
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bank_account_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('provider_txn_ref', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('is_internal_transfer', sa.Boolean(), server_default='0', nullable=False))
        batch_op.create_foreign_key('fk_transactions_bank_account', 'bank_accounts', ['bank_account_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index('ix_transactions_bank_account_id', ['bank_account_id'], unique=False)
        batch_op.create_index('ix_transactions_provider_txn_ref', ['provider_txn_ref'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_index('ix_transactions_provider_txn_ref')
        batch_op.drop_index('ix_transactions_bank_account_id')
        batch_op.drop_constraint('fk_transactions_bank_account', type_='foreignkey')
        batch_op.drop_column('is_internal_transfer')
        batch_op.drop_column('provider_txn_ref')
        batch_op.drop_column('bank_account_id')

    op.drop_index(op.f('ix_bank_sync_logs_account_id'), table_name='bank_sync_logs')
    op.drop_index(op.f('ix_bank_sync_logs_user_id'), table_name='bank_sync_logs')
    op.drop_table('bank_sync_logs')

    op.drop_index(op.f('ix_bank_accounts_consent_id'), table_name='bank_accounts')
    op.drop_index(op.f('ix_bank_accounts_user_id'), table_name='bank_accounts')
    op.drop_table('bank_accounts')

    op.drop_index(op.f('ix_bank_consents_consent_id'), table_name='bank_consents')
    op.drop_index(op.f('ix_bank_consents_consent_handle'), table_name='bank_consents')
    op.drop_index(op.f('ix_bank_consents_user_id'), table_name='bank_consents')
    op.drop_table('bank_consents')
