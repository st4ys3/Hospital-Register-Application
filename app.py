from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort, make_response
import subprocess
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
import secrets
from datetime import datetime, timedelta
import html
from functools import wraps
import uuid
import hashlib

app = Flask(__name__)
# Generate a secure random secret key
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = True  # Changed to False for development
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# Create directories
os.makedirs('static/images', exist_ok=True)
os.makedirs('/app/backup_logs', exist_ok=True)
os.makedirs('/app/yedekler', exist_ok=True)  

# Generate CSRF token
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

# Add CSRF token to all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf_token())

# CSRF protection decorator
def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = session.get('csrf_token')
            form_token = request.form.get('csrf_token')
            
            if not token or not form_token or token != form_token:
                flash("CSRF doğrulama hatası. Lütfen tekrar deneyin.", "danger")
                return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

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

# Check if user owns the resource or has permission
def check_resource_permission(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hastalar WHERE id = %s", (patient_id,))
    hasta = cursor.fetchone()
    conn.close()
    
    if not hasta:
        return False
    
    # Check if the user is the owner of the resource
    return hasta['personel_id'] == session.get('user_id')

def get_db_connection():
    try:
        connection = pymysql.connect(
            host='db',
            user='root',
            password='root',
            database='hospital',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        # Only log critical database connection errors
        print(f"Database connection error: {str(e)}")
        raise

def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user'
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (personel_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Add audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                action VARCHAR(50) NOT NULL,
                resource_type VARCHAR(50) NOT NULL,
                resource_id INT,
                details TEXT,
                ip_address VARCHAR(45),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        raise

# Log user actions
def log_action(action, resource_type, resource_id, details=None):
    if 'user_id' not in session:
        return
    
    try:    
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, resource_type, resource_id, details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            action,
            resource_type,
            resource_id,
            details,
            request.remote_addr
        ))
        
        conn.commit()
        conn.close()
    except Exception:
        # Silently fail on logging errors
        pass

@app.before_request
def ensure_tables_exist():
    if not hasattr(app, 'tables_created'):
        try:
            create_tables()
            app.tables_created = True
        except Exception as e:
            print(f"Failed to create tables: {str(e)}")

@app.route('/')
def index():
    if 'user_id' in session:
        # User is logged in, show welcome page with user info
        return render_template('welcome.html', username=session.get('username'))
    # User is not logged in, show regular index page
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@csrf_protect
def login():
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            # Validate input
            if not username or not password:
                flash("Kullanıcı adı ve şifre gereklidir.", "danger")
                return redirect(url_for('login'))

            # Rate limiting check 
            ip = request.remote_addr
            current_time = datetime.now()
            if 'login_attempts' not in session:
                session['login_attempts'] = 0
                session['login_last_attempt'] = current_time.timestamp()
            
            # If too many attempts, block temporarily
            if session['login_attempts'] >= 5 and (current_time.timestamp() - session['login_last_attempt']) < 300:
                flash("Çok fazla başarısız giriş denemesi. Lütfen 5 dakika sonra tekrar deneyin.", "danger")
                return redirect(url_for('login'))
                
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                # Reset login attempts on successful login
                session['login_attempts'] = 0
                
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user.get('role', 'user')
                session['logged_in'] = True
                
                # Regenerate session ID to prevent session fixation
                session.modified = True
                
                # Log successful login
                log_action('login', 'user', user['id'], 'Successful login')
                
                # Check if there's a next parameter for redirection
                next_page = request.form.get('next') or request.args.get('next')
                if next_page and next_page.startswith('/'):  # Ensure URL is relative
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                # Increment login attempts on failure
                session['login_attempts'] += 1
                session['login_last_attempt'] = current_time.timestamp()
                
                flash("Geçersiz kullanıcı adı veya şifre", "danger")
                return redirect(url_for('login'))
        except Exception as e:
            flash("Giriş sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
            return redirect(url_for('login'))

    # Pass the next parameter to the template
    next_page = request.args.get('next', '')
    return render_template('login.html', next=next_page)

@app.route('/logout')
def logout():
    if 'user_id' in session:
        user_id = session.get('user_id')
        log_action('logout', 'user', user_id, 'User logged out')
    
    # Clear session
    session.clear()
    
    # Set cache control headers to prevent back button from showing authenticated content
    response = make_response(redirect(url_for('index')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/register', methods=['GET', 'POST'])
@csrf_protect
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

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

            # Check password complexity
            if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password):
                flash("Şifre en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.", "danger")
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
            new_user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Log user registration
            log_action('register', 'user', new_user_id, 'New user registered')
            
            flash("Kayıt başarılı. Giriş yapabilirsiniz.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash("Kayıt sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
@csrf_protect
def dashboard():
    if request.method == 'POST':
        try:
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
            new_patient_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Log patient creation
            log_action('create', 'patient', new_patient_id, f'Added new patient: {ad} {soyad}')

            flash("Hasta başarıyla kaydedildi!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash("Hasta kaydı sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
            return redirect(url_for('dashboard'))

    return render_template('dashboard.html')

@app.route('/patients')
@login_required
def patients():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Only show patients created by the current user unless admin
        if session.get('role') == 'admin':
            cursor.execute("""
                SELECT h.*, u.username AS ekleyen 
                FROM hastalar h
                LEFT JOIN users u ON h.personel_id = u.id
                ORDER BY h.id ASC
            """)
        else:
            cursor.execute("""
                SELECT h.*, u.username AS ekleyen 
                FROM hastalar h
                LEFT JOIN users u ON h.personel_id = u.id
                WHERE h.personel_id = %s
                ORDER BY h.id ASC
            """, (session['user_id'],))
            
        hastalar = cursor.fetchall()
        conn.close()
        
        return render_template('patients.html', hastalar=hastalar)
    except Exception as e:
        flash("Hasta listesi alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
        return redirect(url_for('index'))

@app.route('/backup', methods=['GET', 'POST'])
@login_required
@csrf_protect
def backup():
    log = ""

    if request.method == 'POST':
        try:
            # Create backup directory if it doesn't exist
            os.makedirs('/app/yedekler', exist_ok=True)
            os.makedirs('/app/backup_logs', exist_ok=True)
            
            # Create log file if it doesn't exist
            if not os.path.exists('/app/backup.log'):
                open('/app/backup.log', 'a').close()
                
            subprocess.run(['bash', 'backup.sh'], check=True)
            flash("Backup başarıyla alındı.", "success")

            # Log backup action
            log_action('backup', 'database', None, 'Database backup created')

            try:
                with open('/app/backup.log', 'r') as f:
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
@csrf_protect
def delete_patient(patient_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if the patient exists
        cursor.execute("SELECT * FROM hastalar WHERE id = %s", (patient_id,))
        hasta = cursor.fetchone()
        
        if not hasta:
            flash("Hasta bulunamadı.", "danger")
            conn.close()
            return redirect(url_for('patients'))
        
        # Check if the user has permission to delete this patient
        if hasta['personel_id'] != session['user_id'] and session.get('role') != 'admin':
            flash("Bu hastayı silme yetkiniz yok.", "danger")
            conn.close()
            log_action('unauthorized_access', 'patient', patient_id, 'Attempted to delete patient without permission')
            return redirect(url_for('patients'))
        
        # Delete the patient
        cursor.execute("DELETE FROM hastalar WHERE id = %s", (patient_id,))
        conn.commit()
        conn.close()

        # Log patient deletion
        log_action('delete', 'patient', patient_id, f'Deleted patient: {hasta["ad"]} {hasta["soyad"]}')

        flash("Hasta başarıyla silindi!", "success")
        return redirect(url_for('patients'))
    except Exception as e:
        flash("Hasta silinirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
        return redirect(url_for('patients'))

@app.route('/update_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@csrf_protect
def update_patient(patient_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # First check if the patient exists
        cursor.execute("SELECT * FROM hastalar WHERE id = %s", (patient_id,))
        hasta = cursor.fetchone()
        
        if not hasta:
            flash("Hasta bulunamadı.", "danger")
            conn.close()
            return redirect(url_for('patients'))
            
        # Check if the user has permission to update this patient
        if hasta['personel_id'] != session['user_id'] and session.get('role') != 'admin':
            flash("Bu hastayı düzenleme yetkiniz yok.", "danger")
            conn.close()
            log_action('unauthorized_access', 'patient', patient_id, 'Attempted to update patient without permission')
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

            # Log patient update
            log_action('update', 'patient', patient_id, f'Updated patient: {ad} {soyad}')

            flash("Hasta bilgileri başarıyla güncellendi!", "success")
            return redirect(url_for('patients'))

        conn.close()
        return render_template('update_patient.html', hasta=hasta)
    except Exception as e:
        flash("Hasta güncellenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.", "danger")
        return redirect(url_for('patients'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unhandled exception: {str(e)}")
    return render_template('500.html'), 500

@app.after_request
def add_security_headers(response):
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
