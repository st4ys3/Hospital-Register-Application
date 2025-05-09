from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
import subprocess
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
import secrets
from datetime import datetime, timedelta
import html
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secure random secret key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Create directories
os.makedirs('static/images', exist_ok=True)
os.makedirs('/app/backup_logs', exist_ok=True)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Store the requested URL for redirecting after login
            session['next'] = request.url
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
            sikayet TEXT,
            personel_id INT,
            FOREIGN KEY (personel_id) REFERENCES users(id) ON DELETE CASCADE
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
    if 'user_id' in session:
        # User is logged in, show welcome page with user info
        return render_template('welcome.html', username=session.get('username'))
    # User is not logged in, show regular index page
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate input
        if not username or not password:
            flash("Kullanıcı adı ve şifre gereklidir.", "danger")
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['logged_in'] = True
            
            # Check if there's a next parameter for redirection
            next_page = request.form.get('next') or request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash("Geçersiz kullanıcı adı veya şifre", "danger")
            return redirect(url_for('login'))

    # Pass the next parameter to the template
    next_page = request.args.get('next', '')
    return render_template('login.html', next=next_page)

@app.route('/logout')
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptınız.", "success")
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']

        # Validate input
        if not username or not password or not confirm:
            flash("Tüm alanları doldurunuz.", "danger")
            return redirect(url_for('register'))
            
        if len(username) < 4:
            flash("Kullanıcı adı en az 4 karakter olmalıdır.", "danger")
            return redirect(url_for('register'))
            
        if len(password) < 6:
            flash("Şifre en az 6 karakter olmalıdır.", "danger")
            return redirect(url_for('register'))

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
@login_required
def dashboard():
    if request.method == 'POST':
        ad = request.form.get('ad', '').strip()
        soyad = request.form.get('soyad', '').strip()
        tc = request.form.get('tc', '').strip()
        telefon = request.form.get('telefon', '').strip()
        bolum = request.form.get('bolum', '')
        sikayet = request.form.get('sikayet', '').strip()
        
        # Validate input
        if not ad or not soyad or not tc or not telefon or not bolum or not sikayet:
            flash("Tüm alanları doldurunuz.", "danger")
            return redirect(url_for('dashboard'))

        if not re.match(r'^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$', ad) or not re.match(r'^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$', soyad):
           flash("Ad ve soyad sadece harf ve boşluk içerebilir.", "danger")
           return redirect(url_for('dashboard'))
      
        if not tc.isdigit() or len(tc) != 11:
           flash("TC Kimlik numarası 11 haneli ve sadece rakamlardan oluşmalıdır.", "danger")
           return redirect(url_for('dashboard'))
      
        if not re.match(r'^[0-9\+\-\s]+$', telefon):
           flash("Telefon numarası geçerli değil.", "danger")
           return redirect(url_for('dashboard'))

        # Sanitize input
        ad = html.escape(ad)
        soyad = html.escape(soyad)
        sikayet = html.escape(sikayet)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hastalar (ad, soyad, tc, telefon, bolum, sikayet, personel_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (ad, soyad, tc, telefon, bolum, sikayet, session['user_id']))
        conn.commit()
        conn.close()

        flash("Hasta başarıyla kaydedildi!", "success")
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html')

@app.route('/patients')
@login_required
def patients():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.*, u.username AS ekleyen 
        FROM hastalar h
        LEFT JOIN users u ON h.personel_id = u.id
        ORDER BY h.id ASC
    """)
    hastalar = cursor.fetchall()
    conn.close()
    
    return render_template('patients.html', hastalar=hastalar)

@app.route('/backup', methods=['GET', 'POST'])
@login_required
def backup():
    log = ""

    if request.method == 'POST':
        try:
            # Create backup directory if it doesn't exist
            os.makedirs('/home/yedekler', exist_ok=True)
            os.makedirs('/app/backup_logs', exist_ok=True)
            
            # Create log file if it doesn't exist
            if not os.path.exists('/var/log/backup.log'):
                open('/var/log/backup.log', 'a').close()
                
            subprocess.run(['bash', 'backup.sh'], check=True)
            flash("Backup başarıyla alındı.", "success")

            try:
                with open('/var/log/backup.log', 'r') as f:
                    session['log'] = f.read()
            except FileNotFoundError:
                session['log'] = "Log dosyası bulunamadı."
            except PermissionError:
                session['log'] = "Log dosyasına erişim izni yok."

        except subprocess.CalledProcessError as e:
            flash(f"Backup alınırken hata oluştu! Hata kodu: {e.returncode}", "danger")
            session['log'] = ""
        except Exception as e:
            flash(f"Beklenmeyen bir hata oluştu: {str(e)}", "danger")
            session['log'] = ""

        return redirect(url_for('backup'))

    log = session.pop('log', '')

    return render_template('backup.html', log=log)

@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First check if the patient exists and belongs to the current user
    cursor.execute("SELECT * FROM hastalar WHERE id = %s", (patient_id,))
    hasta = cursor.fetchone()
    
    if not hasta:
        flash("Hasta bulunamadı.", "danger")
        conn.close()
        return redirect(url_for('patients'))
    
    # Delete the patient
    cursor.execute("DELETE FROM hastalar WHERE id = %s", (patient_id,))
    conn.commit()
    conn.close()

    flash("Hasta başarıyla silindi!", "success")
    return redirect(url_for('patients'))

@app.route('/update_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def update_patient(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # First check if the patient exists
    cursor.execute("SELECT * FROM hastalar WHERE id = %s", (patient_id,))
    hasta = cursor.fetchone()
    
    if not hasta:
        flash("Hasta bulunamadı.", "danger")
        conn.close()
        return redirect(url_for('patients'))

    if request.method == 'POST':
        ad = request.form.get('ad', '').strip()
        soyad = request.form.get('soyad', '').strip()
        tc = request.form.get('tc', '').strip()
        telefon = request.form.get('telefon', '').strip()
        bolum = request.form.get('bolum', '')
        sikayet = request.form.get('sikayet', '').strip()
        
        # Validate input
        if not ad or not soyad or not tc or not telefon or not bolum or not sikayet:
            flash("Tüm alanları doldurunuz.", "danger")
            return redirect(url_for('update_patient', patient_id=patient_id))

        if not re.match(r'^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$', ad) or not re.match(r'^[A-Za-zÇçĞğİıÖöŞşÜü\s]+$', soyad):
           flash("Ad ve soyad sadece harf ve boşluk içerebilir.", "danger")
           return redirect(url_for('update_patient', patient_id=patient_id))
      
        if not tc.isdigit() or len(tc) != 11:
           flash("TC Kimlik numarası 11 haneli ve sadece rakamlardan oluşmalıdır.", "danger")
           return redirect(url_for('update_patient', patient_id=patient_id))
      
        if not re.match(r'^[0-9\+\-\s]+$', telefon):
           flash("Telefon numarası geçerli değil.", "danger")
           return redirect(url_for('update_patient', patient_id=patient_id))

        # Sanitize input
        ad = html.escape(ad)
        soyad = html.escape(soyad)
        sikayet = html.escape(sikayet)

        cursor.execute("""
            UPDATE hastalar
            SET ad = %s, soyad = %s, tc = %s, telefon = %s, bolum = %s, sikayet = %s
            WHERE id = %s
        """, (ad, soyad, tc, telefon, bolum, sikayet, patient_id))
        conn.commit()
        conn.close()

        flash("Hasta bilgileri başarıyla güncellendi!", "success")
        return redirect(url_for('patients'))

    conn.close()
    return render_template('update_patient.html', hasta=hasta)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
