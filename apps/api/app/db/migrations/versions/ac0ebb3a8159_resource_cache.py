"""resource cache

Revision ID: ac0ebb3a8159
Revises: 9bceebd8664c
Create Date: 2026-08-19 19:49:38.401739

Hand-written (no live DB to autogenerate against yet) — mirrors
docs/02-database-schema.md §4 and app/db/models/resource_cache.py.

Enables pgvector, creates `resource_cache`, then adds the
`generated_resources.cache_id` foreign key that the previous migration
deliberately left off (see its docstring — this is the other half of the
circular FK between the two tables).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ac0ebb3a8159"
down_revision: str | Sequence[str] | None = "9bceebd8664c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "resource_cache",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cache_key", sa.String(), nullable=False, unique=True),
        sa.Column("class_id", sa.Uuid(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("subject_id", sa.Uuid(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("chapter_id", sa.Uuid(), sa.ForeignKey("chapters.id"), nullable=False),
        sa.Column(
            "language", postgresql.ENUM(name="app_language", create_type=False), nullable=False
        ),
        sa.Column(
            "resource_type",
            postgresql.ENUM(name="resource_type", create_type=False),
            nullable=False,
        ),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "canonical_resource_id",
            sa.Uuid(),
            sa.ForeignKey("generated_resources.id"),
            nullable=False,
        ),
        sa.Column("query_embedding", Vector(1536)),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_cache_lookup",
        "resource_cache",
        ["class_id", "subject_id", "chapter_id", "language", "resource_type"],
    )
    op.execute(
        "CREATE INDEX idx_cache_embedding ON resource_cache "
        "USING ivfflat (query_embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_foreign_key(
        "fk_generated_resources_cache_id",
        "generated_resources",
        "resource_cache",
        ["cache_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_generated_resources_cache_id", "generated_resources", type_="foreignkey")
    op.execute("DROP INDEX IF EXISTS idx_cache_embedding")
    op.drop_index("idx_cache_lookup", table_name="resource_cache")
    op.drop_table("resource_cache")
    op.execute("DROP EXTENSION IF EXISTS vector")
