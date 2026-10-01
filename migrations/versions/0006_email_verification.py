"""add email verification metadata

Revision ID: 0006_email_verification
Revises: 0005_billing_subscriptions
"""
from alembic import op
import sqlalchemy as sa


revision = "0006_email_verification"
down_revision = "0005_billing_subscriptions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("users", "email_verified_at")
