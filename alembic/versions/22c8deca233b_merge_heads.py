"""Merge heads

Revision ID: 22c8deca233b
Revises: 20240522_add_admin_and_user_to_userrole_enum, 49797b06ea39
Create Date: 2025-05-22 13:16:55.928468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22c8deca233b'
down_revision: Union[str, None] = ('20240522_add_admin_and_user_to_userrole_enum', '49797b06ea39')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
