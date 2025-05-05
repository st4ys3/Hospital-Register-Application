from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

class Hasta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100))
    soyad = db.Column(db.String(100))
    tc = db.Column(db.String(11))
    telefon = db.Column(db.String(15))
    bolum = db.Column(db.String(100))
    sikayet = db.Column(db.Text)
