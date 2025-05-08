from flask import Flask, render_template, request, redirect, url_for, session, flash
import subprocess
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

os.makedirs('static/images', exist_ok=True)

def get_db_connection():
    return pymysql.connect(
        host='db',
        user='root',
        password='root',
        database='hospital',
        cursorclass=pymysql.cursors.DictCursor
    )

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hastalar (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ad VARCHAR(100),
            soyad VARCHAR(100),
            tc VARCHAR(11),
            telefon VARCHAR(15),
            bolum VARCHAR(100),
            sikayet TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.before_request
def ensure_tables_exist():
    if not hasattr(app, 'tables_created'):
        create_tables()
        app.tables_created = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            flash("Geçersiz kullanıcı adı veya şifre", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("Şifreler uyuşmuyor", "danger")
            return redirect(url_for('register'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Bu kullanıcı adı zaten kayıtlı.", "warning")
            conn.close()
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        conn.close()
        flash("Kayıt başarılı. Giriş yapabilirsiniz.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        ad = request.form['ad'] 
        soyad = request.form['soyad']
        tc = request.form['tc']
        telefon = request.form['telefon']
        bolum = request.form['bolum']
        sikayet = request.form['sikayet']

        import re
        if not re.match(r'^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$', ad) or not re.match(r'^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$', soyad):
           flash("Ad ve soyad sadece harf ve boşluk içerebilir.", "danger")
           return redirect(url_for('dashboard'))
      
        if not tc.isdigit() or len(tc) != 11:
           flash("TC Kimlik numarası 11 haneli ve sadece rakamlardan oluşmalıdır.", "danger")
           return redirect(url_for('dashboard'))
      
        if not re.match(r'^[0-9\+\-\s]+$', telefon):
           flash("Telefon numarası geçerli değil.", "danger")
           return redirect(url_for('dashboard'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hastalar (ad, soyad, tc, telefon, bolum, sikayet)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ad, soyad, tc, telefon, bolum, sikayet))
        conn.commit()
        conn.close()

        flash("Hasta başarıyla kaydedildi!", "success")
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html')


@app.route('/patients')
def patients():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hastalar ORDER BY id DESC")
    hastalar = cursor.fetchall()
    conn.close()
    
    return render_template('patients.html', hastalar=hastalar)


@app.route('/backup', methods=['GET', 'POST'])
def backup():
    log = ""

    if request.method == 'POST':
        try:
            subprocess.run(['bash', 'backup.sh'], check=True)
            flash("Backup başarıyla alındı.", "success")

            with open('/var/log/backup.log', 'r') as f:
                session['log'] = f.read()

        except subprocess.CalledProcessError as e:
            flash(f"Backup alınırken hata oluştu! Hata kodu: {e.returncode}", "error")
            session['log'] = ""

        return redirect(url_for('backup'))

    log = session.pop('log', '')

    return render_template('backup.html', log=log)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
