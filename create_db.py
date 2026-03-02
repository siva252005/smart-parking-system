import sqlite3

conn = sqlite3.connect("parking.db")
cur = conn.cursor()

# Create users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")
# Insert default admin if not exists
cur.execute("SELECT * FROM users WHERE role='admin'")
admin = cur.fetchone()

if not admin:
    cur.execute("""
    INSERT INTO users(name,email,password,role)
    VALUES('Admin','admin@parking.com','admin123','admin')
    """)
# Create slots table
cur.execute("""
CREATE TABLE IF NOT EXISTS slots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT
)
""")

# Create bookings table
cur.execute("""
CREATE TABLE IF NOT EXISTS bookings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    slot_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    total_amount REAL,
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