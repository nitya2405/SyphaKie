"""add output_content to request_records

Revision ID: b0e3c5051278
Revises: h8i9j0k1l2m3
Create Date: 2026-04-28 14:31:36.056106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0e3c5051278'
down_revision: Union[str, None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('request_records', sa.Column('output_content', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('request_records', 'output_content')
