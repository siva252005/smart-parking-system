from datetime import datetime
from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import csv
import io

app = Flask(__name__)
app.secret_key = "secret123"


def connect_db():
    conn = sqlite3.connect("parking.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- HOME ----------------
@app.route('/')
def index():
    return redirect('/login')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO users (name,email,password,role)
        VALUES (?,?,?,?)
        """, (name, email, password, "user"))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                    (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']

            if user['role'] == "admin":
                return redirect('/admin/dashboard')
            else:
                return redirect('/dashboard')

        return "Invalid Credentials"

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- USER DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'user':
        return redirect('/login')

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM slots")
    slots = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", slots=slots)


# ---------------- BOOK SLOT ----------------
@app.route('/book/<int:slot_id>')
def book(slot_id):
    if session.get('role') != 'user':
        return redirect('/login')

    user_id = session.get('user_id')
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO bookings(user_id, slot_id, start_time, status)
    VALUES (?,?,?,?)
    """, (user_id, slot_id, start_time, "Active"))

    cur.execute("UPDATE slots SET status='Occupied' WHERE id=?",
                (slot_id,))

    conn.commit()
    conn.close()

    return redirect('/dashboard')


# ---------------- END BOOKING (BILLING) ----------------
@app.route('/end/<int:booking_id>')
@app.route('/end/<int:booking_id>')
def end_booking(booking_id):
    if session.get('role') != 'user':
        return redirect('/login')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT start_time, slot_id FROM bookings WHERE id=?",
                (booking_id,))
    booking = cur.fetchone()

    if not booking:
        conn.close()
        return redirect('/history')

    start_time = datetime.strptime(booking['start_time'], "%Y-%m-%d %H:%M:%S")
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds() / 3600
    duration = max(1, round(duration))

    rate_per_hour = 20
    total_amount = duration * rate_per_hour

    # 🔥 Simulated Payment Processing
    payment_status = "Paid"   # You can change to "Failed" to test

    cur.execute("""
    UPDATE bookings
    SET end_time=?, total_amount=?, status='Completed'
    WHERE id=?
    """, (end_time.strftime("%Y-%m-%d %H:%M:%S"),
          total_amount, booking_id))

    cur.execute("UPDATE slots SET status='Available' WHERE id=?",
                (booking['slot_id'],))

    conn.commit()
    conn.close()

    return redirect('/history')


# ---------------- BOOKING HISTORY ----------------
@app.route('/history')
def history():
    if session.get('role') != 'user':
        return redirect('/login')

    user_id = session.get('user_id')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM bookings
    WHERE user_id=?
    ORDER BY id DESC
    """, (user_id,))

    bookings = cur.fetchall()
    conn.close()

    return render_template("history.html", bookings=bookings)


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = connect_db()
    cur = conn.cursor()

    # Total slots
    cur.execute("SELECT COUNT(*) as count FROM slots")
    total_slots = cur.fetchone()['count']

    # Occupied slots
    cur.execute("SELECT COUNT(*) as count FROM slots WHERE status='Occupied'")
    occupied = cur.fetchone()['count']

    # Revenue
    cur.execute("SELECT SUM(total_amount) as total FROM bookings WHERE status='Completed'")
    revenue = cur.fetchone()['total'] or 0

    # Total bookings
    cur.execute("SELECT COUNT(*) as count FROM bookings")
    total_bookings = cur.fetchone()['count']

    # Daily revenue trend
    cur.execute("""
    SELECT DATE(end_time) as date, SUM(total_amount) as total
    FROM bookings
    WHERE status='Completed'
    GROUP BY DATE(end_time)
    ORDER BY DATE(end_time)
    """)
    daily_data = cur.fetchall()
    dates = [row['date'] for row in daily_data]
    revenues = [row['total'] for row in daily_data]

    # Peak hour analysis
    cur.execute("""
    SELECT strftime('%H', start_time) as hour, COUNT(*) as count
    FROM bookings
    GROUP BY hour
    ORDER BY hour
    """)
    peak_data = cur.fetchall()
    hours = [row['hour'] for row in peak_data]
    counts = [row['count'] for row in peak_data]

    conn.close()

    occupancy_rate = round((occupied / total_slots) * 100, 2) if total_slots else 0

    return render_template("admin_dashboard.html",
                           total_slots=total_slots,
                           occupied=occupied,
                           revenue=revenue,
                           total_bookings=total_bookings,
                           occupancy_rate=occupancy_rate,
                           dates=dates,
                           revenues=revenues,
                           hours=hours,
                           counts=counts)


# ---------------- ADMIN VIEW ALL BOOKINGS ----------------
@app.route('/admin/bookings')
def admin_bookings():
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT bookings.*, users.name
    FROM bookings
    JOIN users ON bookings.user_id = users.id
    ORDER BY bookings.id DESC
    """)

    bookings = cur.fetchall()
    conn.close()

    return render_template("admin_bookings.html", bookings=bookings)


# ---------------- DOWNLOAD REPORT ----------------
@app.route('/admin/download-report')
def download_report():
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE status='Completed'")
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'User', 'Slot', 'Start', 'End', 'Amount'])

    for row in rows:
        writer.writerow([
            row['id'],
            row['user_id'],
            row['slot_id'],
            row['start_time'],
            row['end_time'],
            row['total_amount']
        ])

    output.seek(0)

    return Response(output,
                    mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment;filename=report.csv"})


if __name__ == '__main__':
    app.run(debug=True)