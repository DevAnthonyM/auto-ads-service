"""create users and cars tables

Revision ID: 001_initial
Revises:
Create Date: 2026-03-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users table ────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # ── Cars table ─────────────────────────────────────────
    op.create_table(
        "cars",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=False,
            comment="Unique identifier derived from carsensor.net listing URL",
        ),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column(
            "price",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            comment="Price in JPY (Japanese Yen)",
        ),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("link", sa.Text(), nullable=False),
        sa.Column(
            "raw_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional scraped fields stored for future use",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=True,
            comment="Soft-delete flag — False when listing is no longer found",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )
    # Individual column indexes
    op.create_index(op.f("ix_cars_external_id"), "cars", ["external_id"], unique=True)
    op.create_index(op.f("ix_cars_make"), "cars", ["make"], unique=False)
    op.create_index(op.f("ix_cars_model"), "cars", ["model"], unique=False)
    op.create_index(op.f("ix_cars_year"), "cars", ["year"], unique=False)
    op.create_index(op.f("ix_cars_price"), "cars", ["price"], unique=False)
    op.create_index(op.f("ix_cars_color"), "cars", ["color"], unique=False)

    # Composite search index for LLM-generated filter queries
    op.create_index("ix_cars_search", "cars", ["make", "model", "year", "price", "color"])


def downgrade() -> None:
    op.drop_index("ix_cars_search", table_name="cars")
    op.drop_index(op.f("ix_cars_color"), table_name="cars")
    op.drop_index(op.f("ix_cars_price"), table_name="cars")
    op.drop_index(op.f("ix_cars_year"), table_name="cars")
    op.drop_index(op.f("ix_cars_model"), table_name="cars")
    op.drop_index(op.f("ix_cars_make"), table_name="cars")
    op.drop_index(op.f("ix_cars_external_id"), table_name="cars")
    op.drop_table("cars")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")