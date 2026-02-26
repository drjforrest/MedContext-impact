"""run_events analytics table

Revision ID: b4c8e1f2a9d6
Revises: a3f9c2d1e8b5
Create Date: 2026-02-25 12:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "b4c8e1f2a9d6"
down_revision = "a3f9c2d1e8b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=True),
        sa.Column("source_channel", sa.String(64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_run_events_started_at",
        "run_events",
        ["started_at"],
        unique=False,
    )
    op.create_index(
        "ix_run_events_outcome",
        "run_events",
        ["outcome"],
        unique=False,
    )
    op.create_index(
        "ix_run_events_source_channel",
        "run_events",
        ["source_channel"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_run_events_source_channel", table_name="run_events")
    op.drop_index("ix_run_events_outcome", table_name="run_events")
    op.drop_index("ix_run_events_started_at", table_name="run_events")
    op.drop_table("run_events")
