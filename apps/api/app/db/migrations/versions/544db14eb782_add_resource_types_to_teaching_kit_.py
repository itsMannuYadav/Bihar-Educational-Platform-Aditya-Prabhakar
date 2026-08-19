"""add resource types to teaching kit requests

Revision ID: 544db14eb782
Revises: 809bbc54750c
Create Date: 2026-08-19 20:13:01.397498

Hand-written (no live DB to autogenerate against yet). Not in the original
docs/02-database-schema.md §3 sketch: /teaching-kit/generate creates the
request row and hands off to /stream (docs/03-api-design.md §4/§10), but
/stream only receives request_id — the requested resource types need to be
persisted somewhere for /stream to know what to generate.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "544db14eb782"
down_revision: str | Sequence[str] | None = "809bbc54750c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "teaching_kit_requests",
        sa.Column("resource_types", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("teaching_kit_requests", "resource_types")
