"""Initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Removed manual enum creation; SQLAlchemy will handle it

    # Create user table
    op.create_table(
        'user',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('role', sa.Enum('owner', 'editor', 'viewer', name='userrole', native_enum=False), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('disabled', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'scheduled', 'in_progress', 'completed', 'cancelled', name='eventstatus'), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=True),
        sa.Column('recurrence_pattern', postgresql.ENUM('none', 'daily', 'weekly', 'monthly', 'yearly', 'custom', name='recurrencepattern'), nullable=True),
        sa.Column('recurrence_end_date', sa.DateTime(), nullable=True),
        sa.Column('recurrence_interval', sa.Integer(), nullable=True),
        sa.Column('recurrence_days', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recurrence_exceptions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_date_range'), 'events', ['start_time', 'end_time'], unique=False)
    op.create_index(op.f('ix_events_status_date'), 'events', ['status', 'start_time'], unique=False)
    op.create_index(op.f('ix_events_title'), 'events', ['title'], unique=False)
    op.create_index(op.f('ix_events_location'), 'events', ['location'], unique=False)
    op.create_index(op.f('ix_events_start_time'), 'events', ['start_time'], unique=False)

    # Create event_participants table
    op.create_table(
        'event_participants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('owner', 'editor', 'viewer', name='userrole', native_enum=False), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('event_id', 'user_id')
    )
    op.create_index(op.f('ix_event_participants_user_role'), 'event_participants', ['user_id', 'role'], unique=False)
    op.create_index(op.f('ix_event_participants_event_role'), 'event_participants', ['event_id', 'role'], unique=False)
    op.create_index(op.f('ix_event_participants_joined_at'), 'event_participants', ['joined_at'], unique=False)

def downgrade() -> None:
    # Drop tables
    op.drop_table('event_participants')
    op.drop_table('events')
    op.drop_table('user')
    # Removed manual enum drop; SQLAlchemy will handle it 