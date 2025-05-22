"""add current_version to events

Revision ID: 49797b06ea39
Revises: add_event_versions_table
Create Date: 2025-05-22 12:17:21.558418

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '49797b06ea39'
down_revision: Union[str, None] = 'add_event_versions_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('events', sa.Column('current_version', sa.Integer(), nullable=True, server_default='1'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('events', 'current_version')
