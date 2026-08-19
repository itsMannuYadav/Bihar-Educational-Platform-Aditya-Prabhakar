"""resource detail tables

Revision ID: 3cebb2b926df
Revises: ac0ebb3a8159
Create Date: 2026-08-19 19:49:39.740082

Hand-written (no live DB to autogenerate against yet) — mirrors
docs/02-database-schema.md §5 and app/db/models/resource_detail.py.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3cebb2b926df"
down_revision: str | Sequence[str] | None = "ac0ebb3a8159"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

question_type = postgresql.ENUM("mcq", "short_answer", "long_answer", "hots", name="question_type")
difficulty = postgresql.ENUM("easy", "moderate", "advanced", name="difficulty")


def upgrade() -> None:
    bind = op.get_bind()
    question_type.create(bind, checkfirst=True)
    difficulty.create(bind, checkfirst=True)

    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resource_id", sa.Uuid(), sa.ForeignKey("generated_resources.id"), nullable=False
        ),
        sa.Column("type", question_type, nullable=False),
        sa.Column("difficulty", difficulty, nullable=False),
        sa.Column("question_text", sa.String(), nullable=False),
        sa.Column("options", sa.JSON()),
        sa.Column("answer", sa.String()),
        sa.Column("explanation", sa.String()),
        sa.Column("is_previous_year", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("idx_questions_resource", "questions", ["resource_id"])

    op.create_table(
        "presentations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resource_id", sa.Uuid(), sa.ForeignKey("generated_resources.id"), nullable=False
        ),
        sa.Column("slide_count", sa.SmallInteger(), nullable=False),
        sa.Column("slides", sa.JSON(), nullable=False),
        sa.Column("pptx_url", sa.String()),
        sa.Column("pdf_url", sa.String()),
        sa.Column("canva_export_ref", sa.String()),
        sa.CheckConstraint("slide_count in (5, 10, 15)", name="ck_presentations_slide_count"),
    )

    op.create_table(
        "audio_resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resource_id", sa.Uuid(), sa.ForeignKey("generated_resources.id"), nullable=False
        ),
        sa.Column("duration_variant", sa.SmallInteger(), nullable=False),
        sa.Column("audio_url", sa.String(), nullable=False),
        sa.Column("transcript", sa.String(), nullable=False),
        sa.Column("tts_provider", sa.String(), nullable=False),
        sa.CheckConstraint(
            "duration_variant in (1, 3, 5)", name="ck_audio_resources_duration_variant"
        ),
    )

    op.create_table(
        "mind_maps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resource_id", sa.Uuid(), sa.ForeignKey("generated_resources.id"), nullable=False
        ),
        sa.Column("structure", sa.JSON(), nullable=False),
        sa.Column("svg_url", sa.String()),
        sa.Column("png_url", sa.String()),
    )

    op.create_table(
        "worksheets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resource_id", sa.Uuid(), sa.ForeignKey("generated_resources.id"), nullable=False
        ),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.Column("pdf_url", sa.String()),
    )


def downgrade() -> None:
    op.drop_table("worksheets")
    op.drop_table("mind_maps")
    op.drop_table("audio_resources")
    op.drop_table("presentations")
    op.drop_index("idx_questions_resource", table_name="questions")
    op.drop_table("questions")

    bind = op.get_bind()
    difficulty.drop(bind, checkfirst=True)
    question_type.drop(bind, checkfirst=True)
