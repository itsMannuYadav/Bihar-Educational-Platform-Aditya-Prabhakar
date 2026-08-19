"""curriculum catalog tables

Revision ID: 80cdb9f2c1d2
Revises: 1f9e46c04954
Create Date: 2026-08-19 19:48:08.807280

Hand-written (no live DB to autogenerate against yet) — mirrors
docs/02-database-schema.md §2 and app/db/models/curriculum.py.

`chapters.syllabus_topics` is `JSON` here rather than the doc's `text[]`
sketch: Postgres arrays have no portable SQLAlchemy DDL compiler for the
in-memory SQLite test DB, unlike `Enum`'s generic CHECK-constraint fallback.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "80cdb9f2c1d2"
down_revision: str | Sequence[str] | None = "1f9e46c04954"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "boards",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False, server_default="Bihar"),
    )

    op.create_table(
        "classes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("board_id", sa.Uuid(), sa.ForeignKey("boards.id"), nullable=False),
        sa.Column("grade", sa.SmallInteger(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("class_id", sa.Uuid(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
    )

    op.create_table(
        "chapters",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("subject_id", sa.Uuid(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sequence_no", sa.SmallInteger()),
        sa.Column("syllabus_topics", sa.JSON()),
    )
    op.create_index("idx_chapters_subject", "chapters", ["subject_id"])


def downgrade() -> None:
    op.drop_index("idx_chapters_subject", table_name="chapters")
    op.drop_table("chapters")
    op.drop_table("subjects")
    op.drop_table("classes")
    op.drop_table("boards")
