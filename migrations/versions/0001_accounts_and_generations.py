"""accounts and saved generations

Revision ID: 0001_accounts_generations
Revises:
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_accounts_generations"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "generations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("style", sa.String(length=64), nullable=False),
        sa.Column("style_label", sa.String(length=120), nullable=False),
        sa.Column("intensity", sa.Integer(), nullable=False),
        sa.Column("output_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("processing_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generations_created_at"), "generations", ["created_at"], unique=False)
    op.create_index(op.f("ix_generations_user_id"), "generations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_generations_user_id"), table_name="generations")
    op.drop_index(op.f("ix_generations_created_at"), table_name="generations")
    op.drop_table("generations")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
