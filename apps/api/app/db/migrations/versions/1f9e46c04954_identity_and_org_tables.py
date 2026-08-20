"""identity and org tables

Revision ID: 1f9e46c04954
Revises:
Create Date: 2026-08-19 17:14:43.448281

Hand-written (no live DB to autogenerate against yet) — mirrors
docs/02-database-schema.md §1 and app/db/models/{school,user}.py.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1f9e46c04954"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = postgresql.ENUM(
    "teacher", "school_admin", "super_admin", name="user_role", create_type=False
)
app_language = postgresql.ENUM("en", "hi", "hinglish", name="app_language", create_type=False)


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    app_language.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "schools",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("udise_code", sa.String(), unique=True),
        sa.Column("state", sa.String(), nullable=False, server_default="Bihar"),
        sa.Column("district", sa.String()),
        sa.Column("block", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("supabase_auth_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), unique=True),
        sa.Column("email", sa.String(), unique=True),
        sa.Column("role", user_role, nullable=False, server_default="teacher"),
        sa.Column("school_id", sa.Uuid(), sa.ForeignKey("schools.id")),
        sa.Column("preferred_language", app_language, nullable=False, server_default="hi"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_users_school", "users", ["school_id"])


def downgrade() -> None:
    op.drop_index("idx_users_school", table_name="users")
    op.drop_table("users")
    op.drop_table("schools")
    app_language.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
