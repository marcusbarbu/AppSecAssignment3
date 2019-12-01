import hashlib
import string
import random
import subprocess
import shlex
import os
from sqlalchemy_utils import create_database
from sqlalchemy.engine.url import make_url
from models import db, User, Login, Query
from myconfig import myconfig
from flask import Flask, render_template, session, request, url_for, redirect

class oldUser:
    def __init__(self, name, pwhash, phone):
        self.uname = name
        self.pwhash = pwhash
        self.phone = phone

app = Flask(__name__)
app.secret_key = "TESTFOOBAR"

app.config.update(myconfig)

users = {}
valid_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def registration():
    global users
    if not 'nonce' in session:
        session['nonce'] = hashlib.sha256(str(random.randint(0,0xFFFFFFF)).encode('ascii')).hexdigest()
    csrf_token = hashlib.sha256(session['nonce'].encode('ascii')).hexdigest()
    if request.method == "POST":
        if not (request.form['uname'] and request.form['pword'] and request.form['2fa']):
            return render_template('register.html', csrf_token=csrf_token, reg_success=False)
        if hashlib.sha256(session['nonce'].encode('ascii')).hexdigest() != request.form['csrf']:
            return render_template('register.html', csrf_token=csrf_token, reg_success=False)

        u = User.query.filter_by(uname=request.form['uname']).first()
        if u:
            return render_template('register.html', csrf_token=csrf_token, reg_success=False)

        u = User(request.form['uname'], request.form['2fa'], request.form['pword'])
        db.session.add(u)
        db.session.commit()
        db.session.refresh(u)
        return render_template('register.html',csrf_token=csrf_token,reg_success=True)

    return render_template('register.html', csrf_token=csrf_token)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not 'nonce' in session:
        session['nonce'] = hashlib.sha256(str(random.randint(0,0xFFFFFFF)).encode('ascii')).hexdigest()

    csrf_token = hashlib.sha256(session['nonce'].encode('ascii')).hexdigest()
    if request.method == 'GET':
        return render_template("login.html", csrf_token=csrf_token)

    csrf = request.form['csrf']
    if csrf != csrf_token:
        return render_template("login.html", message="Incorrect",csrf_token=csrf_token)

    uname = request.form['uname']
    pw = request.form['pword'].encode('utf-8')
    phone = request.form['2fa'].encode('utf-8')
    hash = hashlib.sha256(phone+pw[::-1]).hexdigest()[::-1]
    u = User.query.filter_by(uname=uname).first()
    if not u:
        return render_template("login.html", message="Incorrect",csrf_token=csrf_token)
    u = User.query.filter_by(uname=uname).filter_by(phone=request.form['2fa']).first()
    if not u:
        return render_template("login.html", message="Two-factor failure",csrf_token=csrf_token)
    u = User.query.filter_by(uname=uname).filter_by(phone=request.form['2fa']).filter_by(hash=hash).first()
    if not u:
        return render_template("login.html", message="Incorrect",csrf_token=csrf_token)

    ses_num = hashlib.sha256(str(random.randint(0,0xFFFFFFF)).encode('ascii')).hexdigest() 
    l = Login(u, ses_num+session['nonce'])
    session['token'] = ses_num
    db.session.add(l)
    db.session.commit()
    db.session.refresh(l)

    return render_template("login.html", message="success", csrf_token=csrf_token)

@app.route('/logout')
def logout():
    if not 'nonce' in session or not 'token' in session:
        return redirect(url_for('login'))
    ses = session['token'] + session['nonce']

    l = Login.query.filter_by(session_key=ses).filter_by(active=True).first()

    if not l:
        return redirect(url_for('login'))

    l.active = False
    db.session.add(l)
    db.session.commit()
    db.session.refresh(l)
    return render_template('index.html')


@app.route('/spell_check', methods=['GET','POST'])
def spell_check():
    if not 'nonce' in session or not 'token' in session:
        return redirect(url_for('login'))
    ses = session['token'] + session['nonce']

    l = Login.query.filter_by(session_key=ses).filter_by(active=True).first()

    if not l:
        return redirect(url_for('login'))

    csrf_token = hashlib.sha256(session['nonce'].encode('ascii')).hexdigest()

    if request.method == "GET":
        return render_template("spell_check.html",csrf_token=csrf_token)

    if request.form['csrf'] != csrf_token:
        return redirect(url_for('login'))

    tmpfname = ''.join(random.choices(string.ascii_letters, k=40))
    inputtext = request.form['inputtext']

    with open(tmpfname.encode('ascii'),'w') as tmp:
        tmp.write(inputtext)

    cmd = "./a.out {} wordlist.txt".format(tmpfname) 
    res = subprocess.check_output(shlex.split(cmd)).decode('ascii').split('\n')
    res = ','.join(res)
    os.remove(tmpfname)

    q = Query(l.user, inputtext, res)
    db.session.add(q)
    db.session.commit()
    db.session.refresh(q)

    return render_template('spell_check.html', inwords=request.form['inputtext'], misspelled=res, csrf_token=csrf_token)

@app.route("/history", methods=["GET", "POST"])
def history_overview():
    if not 'nonce' in session or not 'token' in session:
        return redirect(url_for('login'))
    ses = session['token'] + session['nonce']
    l = Login.query.filter_by(session_key=ses).filter_by(active=True).first()
    if not l:
        return redirect(url_for('login'))
    csrf_token = hashlib.sha256(session['nonce'].encode('ascii')).hexdigest()


    if request.method == "POST":
        if not l.user.admin:
            return "Access Denied"
        if request.form['csrf'] != csrf_token:
            return redirect(url_for('login'))
        u = User.query.filter_by(uname=request.form['uname']).first()
        queries = Query.query.filter_by(user=u).all()
        return render_template('admin_history.html', data=[(q.id, q.user.uname) for q in queries], csrf_token=csrf_token)

    if request.method == "GET":
        if l.user.admin == True:
            queries = Query.query.all()
            return render_template('admin_history.html', data=[(q.id, q.user.uname) for q in queries], csrf_token=csrf_token)

        queries = Query.query.filter_by(user=l.user).all()

        return render_template('history.html', data=[q.id for q in queries], count=len(queries))
    return "whut"

@app.route("/history/query<number>")
def history_individual(number):
    if not 'nonce' in session or not 'token' in session:
        return redirect(url_for('login'))
    ses = session['token'] + session['nonce']
    l = Login.query.filter_by(session_key=ses).filter_by(active=True).first()
    if not l:
        return redirect(url_for('login'))

    q = Query.query.filter_by(user=l.user).filter_by(id=number).first()
    if not q:
        if l.user.admin:
            q = Query.query.filter_by(id=number).first()
            if not q:
                return "Access Denied"
        else:
            return "Access Denied"
    return render_template("query_review.html", username=q.user.uname, id=number, inwords = q.inwords, misspelled=q.outwords)

@app.route('/login_history', methods=['GET','POST'])
def history():
    if not 'nonce' in session or not 'token' in session:
        return redirect(url_for('login'))
    ses = session['token'] + session['nonce']
    csrf_token = hashlib.sha256(session['nonce'].encode('ascii')).hexdigest()

    l = Login.query.filter_by(session_key=ses).filter_by(active=True).first()
    if not l:
        return redirect(url_for('login'))
    if not l.user.admin:
        return "denied"

    if request.method == 'GET':
        return render_template("login_history.html", csrf_token=csrf_token)

    if request.form['csrf'] != csrf_token:
        return redirect(url_for('login'))

    sessions = Login.query.filter_by(u_id=request.form['userid']).all()
    data = [(s.id, s.user.uname, s.intime, s.outtime, s.active) for s in sessions]
    return render_template("login_history.html", data=data)


def start_db():
    global app
    url = make_url(app.config['SQLALCHEMY_DATABASE_URI'])
    db.init_app(app)

    try:
        create_database(url)
    except Exception as e:
        print(e)
    db.create_all()
    app.db = db

with app.app_context():
    start_db()
    u = User.query.filter_by(uname="admin").first()
    if not u:
        u = User("admin", "12345678901", "Administrator@1", admin=True)
        db.session.add(u)
        db.session.commit()
        db.session.refresh(u)
    u = User.query.filter_by(uname='aa').first()
    if not u:
        u = User("aa", "1231", "asdf", admin=True)
        db.session.add(u)
        db.session.commit()
        db.session.refresh(u)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)