"""generation job retry metadata

Revision ID: 0003_job_retry_fields
Revises: 0002_generation_jobs
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_job_retry_fields"
down_revision = "0002_generation_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generation_jobs",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="2"),
    )


def downgrade() -> None:
    op.drop_column("generation_jobs", "max_attempts")
    op.drop_column("generation_jobs", "attempt_count")
