"""billing subscriptions and plans

Revision ID: 0005_billing_subscriptions
Revises: 0004_developer_api_keys
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_billing_subscriptions"
down_revision = "0004_developer_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("plan_code", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_customer_id", sa.String(length=255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"], unique=True)
    op.create_index(op.f("ix_subscriptions_provider_customer_id"), "subscriptions", ["provider_customer_id"], unique=False)
    op.create_index(op.f("ix_subscriptions_provider_subscription_id"), "subscriptions", ["provider_subscription_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_subscriptions_provider_subscription_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_provider_customer_id"), table_name="subscriptions")
    op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
