from sqlalchemy import create_engine, text

# Use psycopg2 for sync connection
engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5432/event_management_test')

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64);'))
    conn.commit()

print('alembic_version.version_num column altered to VARCHAR(64)') 