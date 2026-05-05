"""add favorites, template variables, pipeline cron schedule

Revision ID: j0k1l2m3n4o5
Revises: b0e3c5051278
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'j0k1l2m3n4o5'
down_revision = 'b0e3c5051278'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── favorites ─────────────────────────────────────────────────────────────
    op.create_table(
        'favorites',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['request_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'request_id', name='uq_favorites_user_request'),
    )
    op.create_index('ix_favorites_user_id', 'favorites', ['user_id'])

    # ── prompt_templates: variables ───────────────────────────────────────────
    op.add_column('prompt_templates', sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # ── pipelines: cron scheduling ────────────────────────────────────────────
    op.add_column('pipelines', sa.Column('cron_schedule', sa.String(), nullable=True))
    op.add_column('pipelines', sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('pipelines', 'last_run_at')
    op.drop_column('pipelines', 'cron_schedule')
    op.drop_column('prompt_templates', 'variables')
    op.drop_index('ix_favorites_user_id', table_name='favorites')
    op.drop_table('favorites')
