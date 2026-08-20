"""teaching kit requests and generated resources

Revision ID: 9bceebd8664c
Revises: 80cdb9f2c1d2
Create Date: 2026-08-19 19:49:37.052222

Hand-written (no live DB to autogenerate against yet) — mirrors
docs/02-database-schema.md §3 and app/db/models/teaching_kit.py.

`generated_resources.cache_id` is created here as a plain nullable column
with NO foreign key: it references `resource_cache(id)`, but `resource_cache`
doesn't exist until the next migration, and `resource_cache.canonical_resource_id`
references *this* table right back (a genuine circular FK in the schema doc).
The `fk_generated_resources_cache_id` constraint is added via ALTER TABLE in
the resource_cache migration, once both tables exist.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9bceebd8664c"
down_revision: str | Sequence[str] | None = "80cdb9f2c1d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

duration_option = postgresql.ENUM("30", "40", "60", name="duration_option", create_type=False)
teaching_mode = postgresql.ENUM(
    "story",
    "activity",
    "exam",
    "concept",
    "quick_revision",
    name="teaching_mode",
    create_type=False,
)
kit_status = postgresql.ENUM(
    "pending", "generating", "partial", "complete", "failed", name="kit_status", create_type=False
)
resource_type = postgresql.ENUM(
    "lesson_plan",
    "teaching_script",
    "blackboard_notes",
    "local_context",
    "activities",
    "questions",
    "previous_year_questions",
    "worksheet",
    "presentation",
    "mind_map",
    "flowchart",
    "diagram",
    "audio",
    "animation",
    name="resource_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    duration_option.create(bind, checkfirst=True)
    teaching_mode.create(bind, checkfirst=True)
    kit_status.create(bind, checkfirst=True)
    resource_type.create(bind, checkfirst=True)

    op.create_table(
        "teaching_kit_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("class_id", sa.Uuid(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("subject_id", sa.Uuid(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("chapter_id", sa.Uuid(), sa.ForeignKey("chapters.id"), nullable=False),
        sa.Column(
            "language", postgresql.ENUM(name="app_language", create_type=False), nullable=False
        ),
        sa.Column("duration", duration_option, nullable=False),
        sa.Column("teaching_mode", teaching_mode, nullable=False, server_default="concept"),
        sa.Column("raw_query", sa.String()),
        sa.Column("status", kit_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_kit_requests_user", "teaching_kit_requests", ["user_id", "created_at"])

    op.create_table(
        "generated_resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "request_id", sa.Uuid(), sa.ForeignKey("teaching_kit_requests.id"), nullable=False
        ),
        sa.Column("cache_id", sa.Uuid()),
        sa.Column("resource_type", resource_type, nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("file_url", sa.String()),
        sa.Column(
            "language", postgresql.ENUM(name="app_language", create_type=False), nullable=False
        ),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_resources_request", "generated_resources", ["request_id"])
    op.create_index("idx_resources_type", "generated_resources", ["resource_type"])


def downgrade() -> None:
    op.drop_index("idx_resources_type", table_name="generated_resources")
    op.drop_index("idx_resources_request", table_name="generated_resources")
    op.drop_table("generated_resources")
    op.drop_index("idx_kit_requests_user", table_name="teaching_kit_requests")
    op.drop_table("teaching_kit_requests")

    bind = op.get_bind()
    resource_type.drop(bind, checkfirst=True)
    kit_status.drop(bind, checkfirst=True)
    teaching_mode.drop(bind, checkfirst=True)
    duration_option.drop(bind, checkfirst=True)
