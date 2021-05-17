from flask import Flask, request, render_template, session, url_for, redirect
import pyodbc,pandas,geopandas,contextily
import re
import numpy as np
from datetime import date, datetime
import time

app = Flask(__name__)

app.secret_key = 'your secret key'

server = '213.140.22.237\SQLEXPRESS' 
database = 'siriani.andrea' 
username = 'siriani.andrea' 
password = 'xxx123##'  
connection = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)


@app.route('/')
@app.route('/login', methods=['POST','GET'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            msg = 'Logged in successfully !'

            global data
            data = datetime.now().strftime('%d/%m/%Y')
            data = datetime.strptime(data,'%d/%m/%Y')
            global tempo_inizio
            tempo_inizio = datetime.now().strftime('%H:%M:%S')
            cursor.execute('INSERT INTO log (id_utente,data,ora_inizio) VALUES (?,?,?)',(session['id'],data,tempo_inizio))
            cursor.commit()
            #return render_template('Index.html', msg = msg)
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

@app.route('/register', methods=['POST', 'GET'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form :
        username = request.form['username']
        password = request.form['password']
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = ?', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts (username, password) VALUES ( ?, ?)', (username, password))
            cursor.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)


@app.route('/logout')
def logout():
    ora_fine = datetime.now().strftime('%H:%M:%S')
    cursor = connection.cursor()
    cursor.execute('UPDATE log SET ora_fine = (?) WHERE id_utente = (?) AND data = (?) AND ora_inizio = (?)', (ora_fine,session['id'],data,tempo_inizio) )
    cursor.commit()
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/index')
def index():
    df = pandas.read_csv('McDonald.csv')
    df = df[['indirizzo','lat','lon']]
    mc = np.array(df)
    result = ''
    for x in mc:
        result += '[' + str(x[2]) + ',' + str(x[1]) + ',' + "'" + str(x[0]) + "'" + "],"
    result = '[' + result[0:len(result) - 1] + ']'
    return render_template('index.html',df=result)
    

if __name__ == '__main__':
    app.run(debug=True)