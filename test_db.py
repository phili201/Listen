from db import get_db

conn = get_db()

if conn:
    print("Database connection successful.")
    cur = conn.cursor()
    cur.execute("SHOW TABLES;")
    for (table_name,) in cur.fetchall():
        print(table_name)
    cur.close()
    conn.close()
else:
    print("Failed to connect to the database.")