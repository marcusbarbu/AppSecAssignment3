from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, deferred
from hashlib import sha256

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(128), unique=True)
    phone = db.Column(db.String(30))
    hash = db.Column(db.String(256))
    admin = db.Column(db.Boolean, default=False)

    logins = relationship("Login", back_populates="user")
    queries = relationship("Query", back_populates="user")

    def __init__(self, user, phone, password, admin=False):
        self.uname = user
        self.phone = phone
        self.hash = sha256(phone.encode('utf-8')+password.encode('utf-8')[::-1]).hexdigest()[::-1]
        self.admin=admin

class Login(db.Model):
    __tablename__ = "logins"
    id = db.Column(db.Integer, primary_key=True)
    intime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    outtime = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    active = db.Column(db.Boolean, default=True)
    u_id = db.Column(ForeignKey('users.id'))
    session_key = db.Column(db.String(512))
    
    user = relationship("User", back_populates="logins")
    
    def __init__(self, user, key):
        self.u_id = user.id
        self.session_key = key

class Query(db.Model):
    __tablename__ = "queries"
    id = db.Column(db.Integer, primary_key=True)
    u_id = db.Column(ForeignKey('users.id'))
    user = relationship("User", back_populates="queries")
    inwords = db.Column(db.Text)
    outwords = db.Column(db.Text)

    def __init__(self, user, inwords, result):
        self.u_id = user.id
        self.inwords = inwords
        self.outwords = result