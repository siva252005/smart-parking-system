from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def connect_db():
    return sqlite3.connect("parking.db")

# -------- HOME --------

@app.route('/')
def index():
    return render_template("index.html")

# -------- REGISTER --------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                    (name, email, password))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template("register.html")

# -------- LOGIN --------

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
            session['user_id'] = user[0]
            return redirect('/dashboard')

    return render_template("login.html")

# -------- USER DASHBOARD --------

@app.route('/dashboard')
def dashboard():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM slots")
    slots = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", slots=slots)

# -------- BOOK SLOT --------

@app.route('/book/<int:slot_id>')
def book(slot_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("UPDATE slots SET status='Occupied' WHERE id=?",
                (slot_id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

# -------- ADMIN PANEL --------

@app.route('/admin')
def admin():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM slots")
    slots = cur.fetchall()
    conn.close()

    return render_template("admin.html", slots=slots)


if __name__ == '__main__':
    app.run(debug=True)
