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
SELECT n.nspname as enum_schema, t.typname as enum_name, e.enumlabel as enum_value
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid 
JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
WHERE t.typname = 'userrole';
""")
rows = cur.fetchall()

if rows:
    print("userrole enum exists with values:")
    for row in rows:
        print(f"- {row[2]}")
else:
    print("userrole enum does NOT exist in event_management_test database.")

cur.close()
conn.close() 