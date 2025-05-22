"""Create userrole enum type

Revision ID: create_userrole_enum
Revises: initial_migration
Create Date: 2024-05-22 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_userrole_enum'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create userrole enum type
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'user', 'owner', 'editor', 'viewer')")
    
    # Alter user table to use the enum type
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE userrole USING role::userrole")
    
    # Alter event_participants table to use the enum type
    op.execute("ALTER TABLE event_participants ALTER COLUMN role TYPE userrole USING role::userrole")

def downgrade() -> None:
    # Convert columns back to VARCHAR
    op.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE VARCHAR USING role::VARCHAR")
    op.execute("ALTER TABLE event_participants ALTER COLUMN role TYPE VARCHAR USING role::VARCHAR")
    
    # Drop the enum type
    op.execute("DROP TYPE userrole") 