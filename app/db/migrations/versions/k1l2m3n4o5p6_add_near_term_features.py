"""Add request tags, API key spending limits, template is_public

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-05-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'k1l2m3n4o5p6'
down_revision = 'j0k1l2m3n4o5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'request_records',
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.create_index(
        'ix_request_records_tags',
        'request_records',
        ['tags'],
        postgresql_using='gin',
    )

    op.add_column('api_keys', sa.Column('monthly_credit_limit', sa.Integer(), nullable=True))
    op.add_column('api_keys', sa.Column('credits_used_this_month', sa.Integer(), nullable=False, server_default='0'))

    op.add_column('prompt_templates', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('prompt_templates', 'is_public')
    op.drop_column('api_keys', 'credits_used_this_month')
    op.drop_column('api_keys', 'monthly_credit_limit')
    op.drop_index('ix_request_records_tags', table_name='request_records')
    op.drop_column('request_records', 'tags')
