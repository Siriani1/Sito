from flask import Flask, request, render_template, session, url_for, redirect
import pyodbc,pandas,geopandas,contextily
import re

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
            return render_template('Index.html', msg = msg)
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
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/index')
def index():
    mcDonald = pandas.read_csv('McDonald.csv')
    mcDonald = geopandas.GeoDataFrame(mcDonald,geometry=geopandas.points_from_xy(mcDonald["lon"],mcDonald["lat"]))
    mcDonald.crs = 'epsg:4326'
    ax = mcDonald.to_crs(epsg=3857).plot(figsize=(30,22),color='red')
    contextily.add_basemap(ax)
    return render_template('index.html',a=ax)
    

if __name__ == '__main__':
    app.run(debug=True)