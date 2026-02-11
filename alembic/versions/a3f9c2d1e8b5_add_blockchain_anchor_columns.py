"""add blockchain anchor columns to provenance_manifests

Revision ID: a3f9c2d1e8b5
Revises: 8b1b3f0a7c3a
Create Date: 2026-02-10 12:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "a3f9c2d1e8b5"
down_revision = "8b1b3f0a7c3a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "provenance_manifests",
        sa.Column("blockchain_tx_hash", sa.String(), nullable=True, unique=True),
    )
    op.add_column(
        "provenance_manifests",
        sa.Column("blockchain_network", sa.String(), nullable=True),
    )
    op.add_column(
        "provenance_manifests",
        sa.Column(
            "blockchain_anchored_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_provenance_manifests_blockchain_tx_hash",
        "provenance_manifests",
        ["blockchain_tx_hash"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_provenance_manifests_blockchain_tx_hash",
        "provenance_manifests",
        type_="unique",
    )
    op.drop_column("provenance_manifests", "blockchain_anchored_at")
    op.drop_column("provenance_manifests", "blockchain_network")
    op.drop_column("provenance_manifests", "blockchain_tx_hash")
