from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Hasta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@db/hospital'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash("Geçersiz kullanıcı adı veya şifre", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("Şifreler uyuşmuyor", "danger")
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Bu kullanıcı adı zaten kayıtlı.", "warning")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
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

        yeni_hasta = Hasta(ad=ad, soyad=soyad, tc=tc, telefon=telefon, bolum=bolum, sikayet=sikayet)
        db.session.add(yeni_hasta)
        db.session.commit()
        return render_template('dashboard.html', message="Hasta başarıyla kaydedildi!")

    return render_template('dashboard.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)