"""extend_liabilities_with_debt_tracking

Revision ID: d03f52189b34
Revises: c92e742810a1
Create Date: 2026-10-25 15:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd03f52189b34'
down_revision: Union[str, Sequence[str], None] = 'c92e742810a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('liabilities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('debt_type', sa.String(length=32), nullable=False, server_default='payable'))
        batch_op.add_column(sa.Column('counterparty', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('interest_period', sa.String(length=20), nullable=False, server_default='annual'))
        batch_op.add_column(sa.Column('status', sa.String(length=32), nullable=False, server_default='active'))
        batch_op.add_column(sa.Column('loan_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('due_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('repayment_frequency', sa.String(length=32), nullable=False, server_default='monthly'))
        batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('liabilities', schema=None) as batch_op:
        batch_op.drop_column('notes')
        batch_op.drop_column('repayment_frequency')
        batch_op.drop_column('due_date')
        batch_op.drop_column('loan_date')
        batch_op.drop_column('status')
        batch_op.drop_column('interest_period')
        batch_op.drop_column('counterparty')
        batch_op.drop_column('debt_type')
