from code_protection import code_check
import flask
from flask import Flask, flash, request, session, redirect, render_template, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
import pymysql
from pywebpush import webpush, WebPushException
import os
import json
from dotenv import load_dotenv
import sqlite3
import itsdangerous
from itsdangerous import URLSafeTimedSerializer
import smtplib
from flask_mail import Mail, Message
import base64
from flask_cors import CORS

code_check(file_path="main.py", project_folder="/home/philipp/Downloads/Listen APP")
load_dotenv()

app = Flask(__name__)
app.secret_key = 'henvhjnhGZzghihf45nbas'
BASE_URL = "https://listen-1lzv.onrender.com"
ts = URLSafeTimedSerializer(app.secret_key)
DB_PATH = "users.db"
mail = Mail(app)
CORS(app)
maintrance_mode = 'inactive'
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_CLAIMS = {"sub": "mailto:prhode@e-mail.de"}
MARKER = "\u200B\u200C\u200D\u200B\u200B\u200D\u200C\u200B\u200D\u200B\u200C\u200D\u200C\u200B\u200D\u200C\u200B\u200C\u200D\u200D\u200B\u200C\u200D"

subscriptions = [] # TEMPORÄR

app.config['Mail_SERVER'] = 'smtp.ionos.com'
app.config['Mail_PORT'] = 587
app.config['Mail_USERNAME'] = 'prhode@e-mail.de'
app.config['Mail_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
app.config['Mail_USE_TLS'] = True

@app.before_request
def check_logged_in():
    allowed_routes = ['login', 'register', 'not_logged_in', 'static', 'subscribe']
    allowed_maintrance_routes = ['maintrance_mode_route', 'static']
    if request.endpoint not in allowed_routes and ('user_id' not in session):
        return redirect('/not_logged_in')
    if maintrance_mode == 'active' and session.get('maintrance_mode') != 'bypass' and request.endpoint not in allowed_maintrance_routes:
        return "The App is currently in Maintenance Mode. Please try again later."
    

def send_push(subscription_info, message):
    webpush(
        subscription_info=subscription_info,
        data=json.dumps({"message": message}),
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims=VAPID_CLAIMS
    )

def load_user_password():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT password FROM users WHERE user_id = %s", (session['user_id'], ))
    except:
        print('Error')

def register_user(email, password):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, password_hash))
        conn.commit()
        return True
    except pymysql.MySQLError as e:
        print(f"Error registering user: {e}")
        return False

def login_user(email, password_hash, is_verified="0, 1", is_admin="0, 1"):
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password_hash'], password_hash):
            return user
        return None
    except pymysql.MySQLError as e:
        print(f"Error logging in user: {e}")
        return None

def add_list(title, items):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO lists (title, user_id, items) VALUES ( %s, %s, %s)",
            (session['user_id'], title, items)
        )
        conn.commit()
        cursor.execute("SELECT endpoint, p256dh, auth FROM subscriptions WHERE user_id = %s", (session['user_id'],))
        subs = cursor.fetchall()
        for sub in subs:
            send_push({
                "endpoint": sub[0],
                "keys": {
                    "p256dh": sub[1],
                    "auth": sub[2]
                }
            }), f"New list added: {title}"
            return jsonify({"status": "ok"})
        flash('List added successfully!', 'success')
        return redirect('/dashboard')
    except pymysql.MySQLError as e:
        print(f"Error adding list: {e}")
        return None
    
def show_lists():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM lists WHERE user_id = %s", (session['user_id'],))
        lists = cursor.fetchall()
        return lists
    except pymysql.MySQLError as e:
        print(f"Error fetching lists: {e}")
        return []

def generate_verifikation_token(email):
    return ts.dumps(email, salt="email-confirm")

def verify_verifikation_token(token, max_age=3600):
    try:
        email = ts.loads(token, salt="email-confim", max_age=max_age)
    except:
        return None
    
def send_verifikation_email(email):
    token = generate_verifikation_token(email)
    link = f"https://listen-1lzv.onrender.com/verify/{token}"
    msg = Message(
        subject="Email Verifikation",
        recipients=[email],
        body=f"Please verify your Email-Adress here:\n\n{link}\n\nThis Link is valid for one Hour!"
    )
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False
    return True

@app.route('/maintrance_mode', methods=['GET', 'POST'])
def maintrance_mode_route():
    global maintrance_mode
    if request.method == 'POST':
        maintrance_password = request.form['maintrance_password']
        if maintrance_password == os.getenv('MAINTRANCE_PASSWORD'):
            session['maintrance_mode'] = 'bypass'
            return redirect('/')
        else:
            return "Wrong Maintrance Password", 400
    return render_template('maintrance_mode.html')

@app.route('/register_passkey', methods=['GET'])
def register_passkey():
    challenge = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
    session['challenge'] = challenge
    return jsonify({
        'challenge': challenge,
        'rp': {
            'name': 'Listen App',
            'id': 'listen-1lzv.onrender.com'
        },
        'user': {
            'id': str(session['user_id']).encode('utf-8'),
            'name': session['user_id'].encode('utf-8'),
            'displayName': session['user_name'].encode('utf-8')
        },
        'pubKeyCredParams': [
            {'type': 'public-key', 'alg': -7},
        ],
        "timeout": 60000,
        "attestation": "direct"
    })

@app.route('/verify_passkey', methods=['POST'])
def verify_passkey():
    data = request.json
    credential_id = data.get('id')
    email = session['user_email']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET passkey_id=%s WHERE email=%s", (credential_id, email))
    return jsonify({'status': 'ok', 'message': 'Passkey registered successfully'})

@app.route('/update_fingerprint_lock', methods=['POST'])
def update_fingerprint_lock():
    data = request.get_json()
    locked = data.get('locked', False)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET fingerprint_locked=1 WHERE email=%s", (int(locked), session['user_id']))
    conn.commit()
    return jsonify({'status': 'ok', 'message': 'Fingerprint lock updated successfully'})


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if register_user(email, password) and send_verifikation_email(email):
            return redirect('/login')
        else:
            return "Registration failed", 400
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = login_user(email, password, is_verified="0, 1", is_admin="0, 1")
        is_verified = str(user.get('is_verified', '0'))
        is_admin = str(user.get('is_admin', '0'))
        if is_verified == "0":
            return "Please verify your Email-Adress!"
        if is_admin == "1":
            session['is_admin'] = True
            return redirect('/admin_dashboard')
        if user:
            session['user_id'] = email
            return redirect('/')
    return render_template('login.html')

@app.route("/verify/<token>")
def verify(token):
    email = verify_verifikation_token(token)
    if not email:
        return "Token was not vailid"
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE users SET is_verified=1 WHERE email=?", (email, ))
    con.commit()
    return "Your Email-Adress is succesfully verified!"

@app.route('/', methods=['GET'])
def dashboard():
    lists = show_lists()
    return render_template('index.html', lists=lists)

@app.route('/not_logged_in', methods=['POST', 'GET'])
def not_logged_in():
    return render_template('not_logged_in.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    user_id = data["user_id"]
    endpoint = data["endpoint"]
    keys = data["keys"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subscriptions (user_id, endpoint, p256dh, auth) VALUES (%s, %s, %s, %s)",
        (user_id, endpoint, keys["p256dh"], keys["auth"])
    )
    conn.commit()
    return jsonify({"status": "ok"})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

@app.route('/add_list', methods=['GET', 'POST'])
def add_list():
    if request.method == 'POST':
        title = request.form['title']
        items = request.form['items']
        members = request.form.getlist('members')
        if add_list(title, items, members):
            flash('List added successfully!', 'success')
            return redirect('/dashboard')
        else:
            flash('Error adding list', 'error')
    return render_template('add_list.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/change_password', methods=['POST', 'GET'])
def change_password():
    user_password = load_user_password()
    old_password = request.form['old_password']
    new_password_1 = request.form['new_password_1']
    new_password_2 = request.form['new_password_2']
    if old_password in user_password:
        if new_password_1 == new_password_2:
            conn = get_db()
            cursor = conn.cursor()
            try:
               cursor.execute("UPDATE users SET password=new_password_2 WHERE user_id=%s", (session['user_id'], new_password_2, ))
               conn.commit()
               return "New Password succesfully saved"
            except:
                print('Error')
        else:
            return "These Passwords are not the same"
    else:
        return "Wrong old Password"

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect('/not_logged_in')
    return render_template('admin_dashboard.html')

@app.route('/reset_passkey_from_user_admin', methods=['POST', 'GET'])
def reset_passkey_from_user():
    email = request.form['email']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET passkey_id=NULL, public_key=NULL WHERE email=%s", (email,))
    conn.commit()
    return "Passkey reset successfully"

@app.route('/manage_users_admin', methods=['POST', 'GET'])
def manage_users_admin():
    if not session.get('is_admin'):
        return redirect('/not_logged_in')
    email = request.form['email']
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    users = cursor.fetchall()
    return render_template('manage_users_admin.html', email=email, users=users)

@app.route('/get_my_user_admin')
def get_my_user_admin():
    if not session.get('is_admin'):
        return redirect('/not_logged_in')
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT fingerprint_locked FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    return jsonify({
        'fingerprint_locked': user['fingerprint_locked'],
        'email': user['email']
    })

@app.route('/unlock_user_app_admin', methods=['POST', 'GET'])
def unlock_user_app_admin():
    if not session.get('is_admin'):
        return redirect('/not_logged_in')
    email = request.form['email']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET fingerprint_locked=0 WHERE email=%s", (email,))
    conn.commit()
    return jsonify({'success': True, 'message': f'App for {email} unlocked successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)