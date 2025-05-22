import psycopg2

conn = psycopg2.connect(
    dbname="event_management_test",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)
cur = conn.cursor()

cur.execute("""
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'alembic_version'
);
""")
exists = cur.fetchone()[0]

if exists:
    print("alembic_version table exists in event_management_test database.")
else:
    print("alembic_version table does NOT exist in event_management_test database.")

cur.close()
conn.close() 