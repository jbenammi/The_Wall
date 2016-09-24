from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from flask_bcrypt import Bcrypt
import re
app = Flask(__name__)
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app,'wall')
app.secret_key = "13k378987"

def get_user(email):
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': email }
    user = mysql.query_db(user_query, query_data)
    return user


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/wall', methods=['GET', 'POST'])
def wall():
    if request.method == 'GET':
        return render_template('wall.html')

    elif request.method == 'POST':
        message = request.form['message']
        print "hit post on wall"
        print message

        insert_query = "INSERT INTO messages (user_id, message, created_at) VALUES (:user_id, :message, NOW())"
        query_data = {'user_id' : session['id'], 'message': message }
        mysql.query_db(insert_query, query_data)

        return render_template('wall.html')

@app.route('/create_user', methods=['POST'])
def create():
    print "hit"
    print request.form

#validation  / Exist done in view with HTML

    first_name = request.form['first_name']
    last_name = request.form['last_name']

#email validation done in view

    email = request.form['email']
    password = request.form['password']
    confirm = request.form['password_confirm']

    pw_hash = bcrypt.generate_password_hash(password)
    insert_query = "INSERT INTO users (first_name, last_name, email, pw_hash, created_at) VALUES (:first_name, :last_name, :email, :pw_hash, NOW())"
    query_data = { 'first_name': first_name, 'last_name' : last_name, 'email': email,'pw_hash': pw_hash }
    mysql.query_db(insert_query, query_data)

#get/set user before success page

    user = get_user(email)
    session['id'] = user[0]['id']
    session['name'] = user[0]['first_name']

    return redirect('/wall')

@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user(email)
        if len(user) != 0 and bcrypt.check_password_hash(user[0]['pw_hash'], password):
            session['id'] = user[0]['id']
            session['name'] = user[0]['first_name']
            return redirect('/wall')
        else:
            flash("Please try again")
            return redirect('/')
    elif request.method == 'GET':
        return render_template('login.html')

#logout user and clear session

@app.route('/logout', methods=['GET'])
def logout():

    if  'id' in session:
        session.pop('id')
        session.pop('name')
        print session
        return redirect('/')
    else:
        flash("Already logged out")
        return redirect('/')

app.run(debug=True)
