"""Add auto top-up settings and batch generation

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "l2m3n4o5p6q7"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None


def upgrade():
    # Auto top-up: threshold + amount on credits, saved payment method on users
    op.add_column("credits", sa.Column("auto_topup_threshold", sa.Integer(), nullable=True))
    op.add_column("credits", sa.Column("auto_topup_amount", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("stripe_payment_method_id", sa.String(), nullable=True))

    # Batches table for grouped async jobs
    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="running"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_batches_user_id", "batches", ["user_id"])

    # Link jobs to a batch
    op.add_column("jobs", sa.Column("batch_id", postgresql.UUID(as_uuid=True),
        sa.ForeignKey("batches.id", ondelete="SET NULL"), nullable=True))
    op.add_column("jobs", sa.Column("prompt", sa.Text(), nullable=True))
    op.create_index("ix_jobs_batch_id", "jobs", ["batch_id"])


def downgrade():
    op.drop_index("ix_jobs_batch_id", table_name="jobs")
    op.drop_column("jobs", "prompt")
    op.drop_column("jobs", "batch_id")
    op.drop_index("ix_batches_user_id", table_name="batches")
    op.drop_table("batches")
    op.drop_column("users", "stripe_payment_method_id")
    op.drop_column("credits", "auto_topup_amount")
    op.drop_column("credits", "auto_topup_threshold")
