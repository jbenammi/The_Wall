from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from flask_bcrypt import Bcrypt
import re
app = Flask(__name__)
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app,'wall')
app.secret_key = "13k34987"

def get_user(email):
    user_query = "SELECT * FROM users WHERE email = :email LIMIT 1"
    query_data = { 'email': email }
    user = mysql.query_db(user_query, query_data)
    return user


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/success', methods=['POST', 'GET'])
def success():
    return render_template('success.html')

@app.route('/create_user', methods=['POST'])
def create():

    #validation  / Exist done in view with HTML
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    #email validation done in view
    email = request.form['email']
    password = request.form['password']
    confirm = request.form['password_confirm']

    if len(first_name) < 2:
        flash('Only letters and at least 2 characters in your name')
        return redirect('/')
    elif len(last_name) < 2:
        flash('Only letters and at least 2 characters in your last name')
        return redirect('/')
    elif len(password) < 8:
        flash('Password must be at least 8 characters')
        return redirect('/')
    elif not password == confirm:
        flash('Password and Confirmation must match')
        return redirect('/')
    else:
        #create user

        pw_hash = bcrypt.generate_password_hash(password)
        insert_query = "INSERT INTO users (first_name, last_name, email, pw_hash, created_at) VALUES (:first_name, :last_name, :email, :pw_hash, NOW())"
        query_data = { 'first_name': first_name, 'last_name' : last_name, 'email': email,'pw_hash': pw_hash }
        mysql.query_db(insert_query, query_data)

        #get/set user before success page

        user = get_user(email)
        session['id'] = user[0]['id']
        session['name'] = user[0]['first_name']

        return redirect('/success')

@app.route('/login', methods=['POST', 'GET'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = get_user(email)
    if not len(user) == 0 and bcrypt.check_password_hash(user[0]['pw_hash'], password):
        session['id'] = user[0]['id']
        session['name'] = user[0]['first_name']
        return redirect('/success')
    else:
        flash("Please try again")
        return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    if  session['id']:
        session['id'] = ''
        session['name'] = ''
        print session
        return redirect('/')
    else:
        flash("Already logged out")
        return redirect('/')

app.run(debug=True)
