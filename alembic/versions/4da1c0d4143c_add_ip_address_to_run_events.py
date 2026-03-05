"""add ip_address to run_events

Revision ID: 4da1c0d4143c
Revises: b4c8e1f2a9d6
Create Date: 2026-03-01 07:36:21.826736
"""

from alembic import op
import sqlalchemy as sa

revision = '4da1c0d4143c'
down_revision = 'b4c8e1f2a9d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('run_events', sa.Column('ip_address', sa.String(length=45), nullable=True))


def downgrade() -> None:
    op.drop_column('run_events', 'ip_address')
