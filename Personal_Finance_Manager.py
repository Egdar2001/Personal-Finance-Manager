import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_db():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        amount REAL,
                        category TEXT,
                        type TEXT,
                        date TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "Username already exists!"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if 'user_id' in session:
        user_id = session['user_id']
        amount = request.form['amount']
        category = request.form['category']
        trans_type = request.form['type']
        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transactions (user_id, amount, category, type, date) VALUES (?, ?, ?, ?, ?)",
                       (user_id, amount, category, trans_type, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
    return redirect('/dashboard')

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, category, type, date FROM transactions WHERE user_id=?", (user_id,))
    transactions = cursor.fetchall()
    conn.close()
    return render_template('transactions.html', transactions=transactions)

@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        new_amount = request.form['amount']
        new_category = request.form['category']
        new_type = request.form['type']
        
        cursor.execute("UPDATE transactions SET amount=?, category=?, type=? WHERE id=? AND user_id=?", 
                       (new_amount, new_category, new_type, transaction_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect('/transactions')

    cursor.execute("SELECT id, amount, category, type FROM transactions WHERE id=? AND user_id=?", 
                   (transaction_id, session['user_id']))
    transaction = cursor.fetchone()
    conn.close()

    if transaction:
        return render_template('edit_transaction.html', transaction=transaction)
    else:
        return "Transaction not found", 404


@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (transaction_id, user_id))
    conn.commit()
    conn.close()
    return redirect('/transactions')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
