import psycopg2

conn = psycopg2.connect(
    dbname="event_management_test",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)
cur = conn.cursor()

# Create userrole enum type
cur.execute("CREATE TYPE userrole AS ENUM ('admin', 'user', 'owner', 'editor', 'viewer')")

# Alter user table to use the enum type
cur.execute("ALTER TABLE \"user\" ALTER COLUMN role TYPE userrole USING role::userrole")

# Alter event_participants table to use the enum type
cur.execute("ALTER TABLE event_participants ALTER COLUMN role TYPE userrole USING role::userrole")

conn.commit()
print("userrole enum created and tables altered successfully.")

cur.close()
conn.close() 