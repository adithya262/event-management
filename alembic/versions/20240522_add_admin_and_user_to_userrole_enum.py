"""
Add 'admin' and 'user' to userrole enum

Revision ID: 20240522_add_admin_and_user_to_userrole_enum
Revises: initial_migration
Create Date: 2024-05-22
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240522_add_admin_and_user_to_userrole_enum'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Add 'admin' and 'user' to the userrole enum type
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                CREATE TYPE userrole AS ENUM ('admin', 'user', 'viewer', 'editor', 'owner');
            ELSE
                IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'admin' AND enumtypid = 'userrole'::regtype) THEN
                    ALTER TYPE userrole ADD VALUE 'admin';
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'user' AND enumtypid = 'userrole'::regtype) THEN
                    ALTER TYPE userrole ADD VALUE 'user';
                END IF;
            END IF;
        END$$;
    """)

def downgrade():
    # Downgrade is not supported for removing enum values in PostgreSQL
    pass 