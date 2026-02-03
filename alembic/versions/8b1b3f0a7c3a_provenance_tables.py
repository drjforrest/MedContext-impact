"""provenance tables

Revision ID: 8b1b3f0a7c3a
Revises: 5b287932865b
Create Date: 2026-01-27 13:05:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "8b1b3f0a7c3a"
down_revision = "5b287932865b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provenance_manifests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("image_id", sa.UUID(), nullable=True),
        sa.Column("image_hash", sa.String(), nullable=False),
        sa.Column("manifest_label", sa.String(), nullable=True),
        sa.Column(
            "manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("signature_status", sa.String(), nullable=True),
        sa.Column("validation_state", sa.String(), nullable=True),
        sa.Column(
            "validation_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["image_id"], ["image_submissions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provenance_manifests_image_hash",
        "provenance_manifests",
        ["image_hash"],
        unique=True,
    )
    op.create_table(
        "provenance_blocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("manifest_id", sa.UUID(), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("previous_hash", sa.String(), nullable=True),
        sa.Column("block_hash", sa.String(), nullable=False),
        sa.Column("observation_type", sa.String(), nullable=False),
        sa.Column(
            "observation_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["manifest_id"], ["provenance_manifests.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "manifest_id", "block_number", name="uq_provenance_blocks_manifest_block"
        ),
    )
    op.create_index(
        "ix_provenance_blocks_manifest_id", "provenance_blocks", ["manifest_id"]
    )


def downgrade() -> None:
    op.drop_table("provenance_blocks")
    op.drop_index(
        "ix_provenance_manifests_image_hash", table_name="provenance_manifests"
    )
    op.drop_table("provenance_manifests")
    op.drop_table("provenance_manifests")
    op.drop_table("provenance_manifests")
