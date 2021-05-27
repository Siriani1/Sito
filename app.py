#importo tutte le librerie necessarie 
from flask import Flask, request, render_template, session, url_for, redirect
import pyodbc,pandas
import pandas
import re
import numpy as np
from datetime import datetime
import json


app = Flask(__name__)

app.secret_key = 'your secret key'

#collegamento con sql server
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
        #prendo le informazioni che ha inserito l'utente 
        username = request.form['username']
        password = request.form['password']
        cursor = connection.cursor()
        #faccio una select dove prendo tutti gli account e vedo se le informazione combinano
        cursor.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (username, password, ))
        account = cursor.fetchone()
        #se l'account esiste l'utente si logga
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            msg = 'Logged in successfully !'

            #quando l'utente si logga prendo la data e l'ora e poi la inserisco nel database
            #global serve per riprendere la variabile in altre funzioni
            global data
            data = datetime.now().strftime('%d/%m/%Y')
            data = datetime.strptime(data,'%d/%m/%Y')
            global tempo_inizio
            tempo_inizio = datetime.now().strftime('%H:%M:%S')
            cursor.execute('INSERT INTO log (id_utente,data,ora_inizio) VALUES (?,?,?)',(session['id'],data,tempo_inizio))
            cursor.commit()
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
        #faccio una select e vedo se i campi combinano 
        cursor.execute('SELECT * FROM accounts WHERE username = ?', (username, ))
        account = cursor.fetchone()
        #faccio un if dove controllo se l'account esiste o ci sono caratteri speciali
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password:
            msg = 'Please fill out the form !'
        else:
            #se l'account non esiste lo inserisco nel database
            cursor.execute('INSERT INTO accounts (username, password) VALUES ( ?, ?)', (username, password))
            cursor.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)


@app.route('/logout')
def logout():
    #il try serve perchè se ci sono degli errori fa ritornare l'utente al login
    try:
        #prendo l'ora di quando l'utente esce e la inserisco nel database
        global ora_fine
        ora_fine = datetime.now().strftime('%H:%M:%S')
        cursor = connection.cursor()
        cursor.execute('UPDATE log SET ora_fine = (?) WHERE id_utente = (?) AND data = (?) AND ora_inizio = (?)', (ora_fine,session['id'],data,tempo_inizio))
        cursor.commit()
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
        return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))


@app.route('/index', methods=['POST', 'GET'])
def index():
    #il try serve perchè se ci sono degli errori fa ritornare l'utente al login
    try:
        cursor = connection.cursor()
        #prendo tutte le informazione dei mcdonald dal database
        df = 'SELECT * FROM dbo.McDonald'
        df = pandas.read_sql_query(df,connection)
        df = df[['indirizzo','lat','lon']]
        
        mc = np.array(df)
        result = ''
        #trasformo le informazione in un array manualmente a dal np array prendo quello che mi serve, per farlo capire a javaScript
        for x in mc:
            result += '[' + str(x[2]) + ',' + str(x[1]) + ',' + "'" + str(x[0]) + "'" + "],"
        #lo faccio diventare un array multidimensionale e -1 serve per togliere l'ultima virgola
        result = '[' + result[0:len(result) - 1] + ']'

        #prendo dal database l'id dell'utente collegato
        cursor.execute('SELECT TOP 1 * FROM log WHERE id_utente = (?) ORDER BY data DESC,ora_inizio DESC', (session['id']))
        global utente
        utente = cursor.fetchone()
        

        
        #faccio la richiesta a XMLHTTPREREQUEST e le decodiamo da bite a stringhe
        data = request.data.decode('utf-8')
        
        #se il dato non è vuoto inizio il procedimento
        if data != "":
            #converto da jsno a python
            data = json.loads(data)
            #separo il contenuto all'interno di data in due variabili
            lat,lon = data['lat'],data['lng']
            #seleziono il McDonald che ha quelle cordinate 
            cursor.execute('SELECT * FROM McDonald WHERE lat = (?) AND lon = (?)', (lat,lon))
            Mc = cursor.fetchone()
            #inserisco nel database l'id dell'utente e l'id del McDonald
            cursor.execute('INSERT INTO seleziona (idMc, idLog) VALUES ( ?, ?)', (Mc[0],utente[0]))
            cursor.commit()
        

        return render_template('index.html',df=result)
    except:
        return redirect(url_for('login'))
    
@app.route('/log', methods=['POST', 'GET'])
def log():
    cursor = connection.cursor()
    data = request.data.decode('utf-8')
    #print(data)
    #divido data in due parti divisi dai : e prendo la prima parte
    lat = data.split(":")[0]
    #prendo la seconda parte
    lon = data.split(":")[1]
    #tolgo da lat gli apici iniziali
    lat = lat[1:]
    #tolgo da lon gli apici finali
    lon = lon[:-1]
    #inserisco lat e lon dell'utente nel database
    cursor.execute('UPDATE log SET lat = (?), lon = (?)  WHERE id = (?)', (lat,lon,utente[0]))
    cursor.commit()
    return lat


@app.route('/secretLogin', methods=['POST', 'GET'])
def secretLogin():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = connection.cursor()
        cursor.execute('SELECT * from secretLogin WHERE username = (?) AND  password = (?)', (username,password))
        secretAccount = cursor.fetchone()
        if secretAccount:
            return redirect(url_for('Utenti'))
        else:
            msg = 'username/password incorretti'
    return render_template('secretLogin.html', msg=msg)

@app.route('/Utenti')
def Utenti():
    #seleziono la tabella degli utenti e passo le informazioni nel file html
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM accounts')
    utenti = cursor.fetchall()

    return render_template('Utenti.html', utenti=utenti,)

@app.route('/Log')
def Log():
    #seleziono la tabella degli utenti e passo le informazioni nel file html
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM log')
    log = cursor.fetchall()

    return render_template('Log.html', log=log)

@app.route('/Seleziona')
def Seleziona():
    #faccio una select con inner join e poi passo le informazioni al file html
    cursor = connection.cursor()
    cursor.execute('''select accounts.username, log.data, log.ora_inizio, log.ora_fine, log.lat, log.lon, McDonald.indirizzo
    from log  INNER JOIN Seleziona ON log.id = Seleziona.idLog
    INNER JOIN McDonald ON Seleziona.idMc = McDonald.id
    INNER JOIN accounts ON accounts.id = log.id_utente''')
    seleziona = cursor.fetchall()

    return render_template('Seleziona.html', seleziona=seleziona)




if __name__ == '__main__':
    app.run(debug=True)