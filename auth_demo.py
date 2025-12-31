# Ce script ajoute une authentification admin par mot de passe avec session Flask.
# Il utilise werkzeug.security pour le hash, et protège toutes les routes sensibles.
# À intégrer dans main.py (ou à fusionner avec ton code existant)

import os
import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')  # À changer en prod !
DB_PATH = 'data/fleet.db'

# --- Helpers DB ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_admin_table():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

# --- Authentification ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/init-admin', methods=['GET', 'POST'])
def init_admin():
    create_admin_table()
    conn = get_db()
    cur = conn.execute('SELECT COUNT(*) FROM admin')
    if cur.fetchone()[0] > 0:
        conn.close()
        return 'Admin déjà initialisé.'
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hash_pw = generate_password_hash(password)
        try:
            conn.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', (username, hash_pw))
            conn.commit()
            flash('Admin créé. Connectez-vous.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Erreur : ' + str(e))
    conn.close()
    return render_template('init_admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.execute('SELECT password_hash FROM admin WHERE username = ?', (username,))
        row = cur.fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        flash('Identifiants invalides')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('index.html')

@app.route('/admin')
@login_required
def admin_panel():
    return render_template('admin_orgs.html')

# --- Pour test rapide ---
if __name__ == '__main__':
    app.run(debug=True)
