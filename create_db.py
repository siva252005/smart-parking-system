import sqlite3

conn = sqlite3.connect("parking.db")
cur = conn.cursor()

# Create users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
""")

# Create slots table
cur.execute("""
CREATE TABLE IF NOT EXISTS slots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT
)
""")

# Check slot count
cur.execute("SELECT COUNT(*) FROM slots")
count = cur.fetchone()[0]

if count == 0:
    for i in range(10):
        cur.execute("INSERT INTO slots(status) VALUES('Available')")

conn.commit()
conn.close()

print("Database created successfully!")