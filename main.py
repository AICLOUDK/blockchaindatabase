from flask import Flask, render_template, redirect, url_for, request, session, flash
import os
import sqlite3
from datetime import datetime
from block import create_block

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize database
def init_db():
    conn = sqlite3.connect('blockchain.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    userid INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receiver TEXT,
                    amount REAL,
                    timestamp TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS blockchain (
                    id INTEGER PRIMARY KEY,
                    block_hash TEXT,
                    previous_hash TEXT
                )''')
    # Genesis block
    c.execute("SELECT * FROM blockchain WHERE id=1")
    if not c.fetchone():
        c.execute("INSERT INTO blockchain (id, block_hash, previous_hash) VALUES (1, '', '')")
    conn.commit()
    conn.close()

init_db()

# Helper functions
def get_db():
    return sqlite3.connect('blockchain.db')

def hash_content(content):
    import hashlib
    return hashlib.md5(content.encode()).hexdigest()

def get_latest_hash():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT block_hash FROM blockchain WHERE id=1")
    hash_value = c.fetchone()[0]
    conn.close()
    return hash_value

def update_latest_hash(new_hash):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE blockchain SET block_hash=? WHERE id=1", (new_hash,))
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    blockchain_status = "Valid"  # Here, add real validation if needed
    latest_hash = get_latest_hash()
    transactions = []
    if 'user' in session:
        user = session['user']
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM transactions WHERE sender=? OR receiver=?", (user, user))
        transactions = c.fetchall()
        conn.close()
    return render_template('index.html', blockchain_status=blockchain_status, latest_hash=latest_hash, transactions=transactions)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        if len(pin) !=8 or not pin.isdigit():
            flash("PIN must be exactly 8 digits.")
            return redirect(url_for('register'))
        hashed_pin = hash_content(pin)
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pin))
            conn.commit()
            conn.close()
            flash("Registration successful. Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        hashed_pin = hash_content(pin)
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and user[2] == hashed_pin:
            session['user'] = username
            flash("Logged in successfully.")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out.")
    return redirect(url_for('index'))

@app.route('/create_transaction', methods=['POST'])
def create_transaction():
    if 'user' not in session:
        flash("Please login first.")
        return redirect(url_for('login'))
    sender = session['user']
    receiver = request.form['receiver']
    amount = float(request.form['amount'])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Create new block
    data = {
        'sender': sender,
        'receiver': receiver,
        'amount': amount,
        'timestamp': timestamp
    }
    previous_hash = get_latest_hash()
    new_block = create_block(data, previous_hash)
    # Save transaction
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO transactions (sender, receiver, amount, timestamp) VALUES (?, ?, ?, ?)",
              (sender, receiver, amount, timestamp))
    conn.commit()
    conn.close()
    # Update blockchain hash
    update_latest_hash(new_block['hash'])
    flash("Transaction recorded.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
