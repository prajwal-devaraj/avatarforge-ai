"""asynchronous generation jobs

Revision ID: 0002_generation_jobs
Revises: 0001_accounts_generations
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_generation_jobs"
down_revision = "0001_accounts_generations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("access_token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("style", sa.String(length=64), nullable=False),
        sa.Column("intensity", sa.Integer(), nullable=False),
        sa.Column("engine", sa.String(length=24), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("input_path", sa.String(length=500), nullable=False),
        sa.Column("input_name", sa.String(length=255), nullable=False),
        sa.Column("input_mime_type", sa.String(length=100), nullable=False),
        sa.Column("output_path", sa.String(length=500), nullable=True),
        sa.Column("output_mime_type", sa.String(length=100), nullable=True),
        sa.Column("download_name", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("generation_id", sa.String(length=36), nullable=True),
        sa.Column("processing_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generation_jobs_created_at"), "generation_jobs", ["created_at"], unique=False)
    op.create_index(op.f("ix_generation_jobs_status"), "generation_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_generation_jobs_user_id"), "generation_jobs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_generation_jobs_user_id"), table_name="generation_jobs")
    op.drop_index(op.f("ix_generation_jobs_status"), table_name="generation_jobs")
    op.drop_index(op.f("ix_generation_jobs_created_at"), table_name="generation_jobs")
    op.drop_table("generation_jobs")
