"""personas library and analytics

Revision ID: 809bbc54750c
Revises: 3cebb2b926df
Create Date: 2026-08-19 19:49:41.067353

Hand-written (no live DB to autogenerate against yet) — mirrors
docs/02-database-schema.md §6-8 and app/db/models/{persona,saved_lesson,analytics}.py.
Small, independent tables, bundled into one migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "809bbc54750c"
down_revision: str | Sequence[str] | None = "3cebb2b926df"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

analytics_event_type = postgresql.ENUM(
    "search",
    "kit_generated",
    "resource_viewed",
    "resource_downloaded",
    "resource_regenerated",
    "cache_hit",
    "cache_miss",
    name="analytics_event_type",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "teaching_personas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("characteristics", sa.JSON(), nullable=False),
        sa.Column("prompt_fragment", sa.String(), nullable=False),
    )

    op.create_table(
        "saved_lessons",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "request_id", sa.Uuid(), sa.ForeignKey("teaching_kit_requests.id"), nullable=False
        ),
        sa.Column("note", sa.String()),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        "CREATE UNIQUE INDEX idx_saved_unique ON saved_lessons (user_id, request_id) "
        "WHERE deleted_at IS NULL"
    )

    bind = op.get_bind()
    analytics_event_type.create(bind, checkfirst=True)

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("school_id", sa.Uuid(), sa.ForeignKey("schools.id")),
        sa.Column("event_type", analytics_event_type, nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_analytics_type_time", "analytics_events", ["event_type", "created_at"])
    op.create_index("idx_analytics_school", "analytics_events", ["school_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_analytics_school", table_name="analytics_events")
    op.drop_index("idx_analytics_type_time", table_name="analytics_events")
    op.drop_table("analytics_events")
    analytics_event_type.drop(op.get_bind(), checkfirst=True)

    op.execute("DROP INDEX IF EXISTS idx_saved_unique")
    op.drop_table("saved_lessons")

    op.drop_table("teaching_personas")
