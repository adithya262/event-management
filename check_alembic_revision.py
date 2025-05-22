import psycopg2

conn = psycopg2.connect(
    dbname="event_management_test",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)
cur = conn.cursor()

cur.execute("SELECT version_num FROM alembic_version;")
rows = cur.fetchall()

if rows:
    print(f"Current alembic revision(s): {[row[0] for row in rows]}")
else:
    print("No revision found in alembic_version table.")

cur.close()
conn.close() 