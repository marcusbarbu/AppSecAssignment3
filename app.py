import hashlib
import string
import random
import subprocess
import shlex
import os
from flask import Flask, render_template, session, request, url_for, redirect

class User:
    def __init__(self, name, pwhash, phone):
        self.uname = name
        self.pwhash = pwhash
        self.phone = phone

app = Flask(__name__)
app.secret_key = "TESTFOOBAR"

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
        if request.form['uname'] in users.keys():
            return render_template('register.html', csrf_token=csrf_token, reg_success=False)
        else:
            u = User(request.form['uname'], hashlib.sha256(request.form['pword'].encode('ascii')).hexdigest(), request.form['2fa'])
            users[request.form['uname']] = u
            return render_template('register.html',csrf_token=csrf_token,reg_success=True)
    return render_template('register.html', csrf_token=csrf_token)

@app.route('/login', methods=['GET', 'POST'])
def login():
    global users, valid_sessions
    if not 'nonce' in session:
        session['nonce'] = hashlib.sha256(str(random.randint(0,0xFFFFFFF)).encode('ascii')).hexdigest()

    csrf_token = hashlib.sha256(session['nonce'].encode('ascii')).hexdigest()
    if request.method == 'GET':
        return render_template("login.html", csrf_token=csrf_token)

    csrf = request.form['csrf']
    if csrf != csrf_token:
        return render_template("login.html", message="Incorrect",csrf_token=csrf_token)

    uname = request.form['uname']
    if not uname in users.keys():
        return render_template("login.html", message="Incorrect",csrf_token=csrf_token)
    user = users[uname]
    pw = request.form['pword'].encode('ascii') 
    pw = hashlib.sha256(pw).hexdigest()
    phone = request.form['2fa']
    if pw != user.pwhash:
        return render_template("login.html", message="Incorrect",csrf_token=csrf_token)
    elif phone != user.phone:
        return render_template("login.html", message="Two-factor failure",csrf_token=csrf_token)
    ses_num = hashlib.sha256(str(random.randint(0,0xFFFFFFF)).encode('ascii')).hexdigest() 
    valid_sessions[ses_num + session['nonce']] = user
    session['token'] = ses_num
    return render_template("login.html", message="success", csrf_token=csrf_token)

@app.route('/spell_check', methods=['GET','POST'])
def spell_check():
    global valid_sessions, users
    if not 'nonce' in session or not 'token' in session:
        return redirect(url_for('login'))
    ses = session['token'] + session['nonce']
    if not ses in valid_sessions:
        return redirect(url_for('login'))
    csrf_token = hashlib.sha256(session['nonce'].encode('ascii')).hexdigest()

    if request.method == "GET":
        return render_template("spell_check.html",csrf_token=csrf_token)

    if request.form['csrf'] != csrf_token:
        return redirect(url_for('login'))

    tmpfname = ''.join(random.choices(string.ascii_letters, k=40))
    with open(tmpfname.encode('ascii'),'w') as tmp:
        tmp.write(request.form['inputtext'])
    cmd = "./a.out {} wordlist.txt".format(tmpfname) 
    res = subprocess.check_output(shlex.split(cmd)).decode('ascii').split('\n')
    res = ','.join(res)
    print(res)

    os.remove(tmpfname)

    return render_template('spell_check.html', inwords=request.form['inputtext'], misspelled=res, csrf_token=csrf_token)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)