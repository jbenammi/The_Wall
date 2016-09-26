from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from datetime import datetime, timedelta
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

def get_messages():
    user_query = "SELECT users.id, users.first_name, users.last_name, messages.message, messages.id as message_id, messages.created_at FROM  users JOIN messages ON users.id = messages.user_id ORDER BY created_at DESC"

    messages = mysql.query_db(user_query)
    return messages

def get_comments():
    user_query = "Select comments.id as comment_id, users.first_name, comments.comment, comments.created_at, comments.message_id from comments JOIN users ON comments.user_id = users.id ORDER BY created_at DESC "

    comments = mysql.query_db(user_query)
    return comments

def get_stats():
    return stats

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/wall', methods=['GET', 'POST'])
def wall():
    if request.method == 'GET':

        #get current user dictionary
        current_user = get_user(session['email'])

        #get basic scrubbed info of user
        name = current_user[0]['first_name']

        #get all messages
        messages = get_messages()

        #get all comments
        comments = get_comments()


        return render_template('wall.html', current_name = name, all_messages = messages, all_comments = comments)

    elif request.method == 'POST':
        print ("/wall method post")


        if 'message' in request.form:
            print ("/wall method post message")
            #get message from view
            message = request.form['message']

            #insert message intp db
            insert_query = "INSERT INTO messages (user_id, message, created_at) VALUES (:user_id, :message, NOW())"
            query_data = {'user_id' : session['id'], 'message': message }
            mysql.query_db(insert_query, query_data)

            #get current user dictionary
            current_user = get_user(session['email'])

            #get basic scrubbed info of user
            name = current_user[0]['first_name']

            #get all messages
            messages = get_messages()
            print messages

            return redirect('/wall')

        elif 'comment' in request.form:
            print ("/wall method post comment")

            #get comment from view
            comment = request.form['comment']
            message_id = request.form['message_id']

            #insert comment intp db
            insert_query = "INSERT INTO comments(comment, created_at, updated_at, message_id, user_id) VALUES (:comment, NOW(), NOW(), (SELECT id FROM messages WHERE id = :message_id), :user_id)"

            query_data = {'comment': comment, 'message_id' : message_id, 'user_id' : session['id'] }
            mysql.query_db(insert_query, query_data)


            return redirect('/wall')

        #Delete messages which is also cascaded to comments
        elif 'delete-message' in request.form:
            print "delete-message hit"
            message_id = request.form['message_id']

            #get message details from db
            insert_query =  "select users.id as user_id, messages.id as message_id, messages.created_at FROM users JOIN messages ON users.id = messages.user_id WHERE messages.id = :message_id"
            query_data = {'message_id': message_id}
            message_info = mysql.query_db(insert_query, query_data)

            #time logic
            then = datetime.now() - timedelta(hours = int(message_info[0]['created_at'].strftime('%H')))
            now = datetime.now()

            #run validation and delete
            if message_info[0]['user_id'] != session['id']:
                flash("Sorry, you can only delete your own posts!")

            elif message_info[0]['user_id'] == session['id']:
                insert_query =  "DELETE FROM messages WHERE id = :message_id"
                query_data = {'message_id': message_id}
                mysql.query_db(insert_query, query_data)

                flash("The post have been deleted!")

            elif (now - then) > timedelta(hours > .5):
                 flash("Sorry, you post is more than 30 minutes old")

            return redirect('/wall')

        #Delete comment and not the messages
        elif 'delete-comment' in request.form:
            comment_id = request.form['comment_id']

            #select comment from id out of db
            insert_query = "SELECT comments.id AS comments_id, user_id FROM comments WHERE comments.id = :comments_id"
            query_data = {'comments_id': comment_id}
            comments_check = mysql.query_db(insert_query, query_data)


            #comment deleting logic if user is owner of comment
            if comments_check[0]['user_id']!= session['id']:
                flash("Sorry, you can only delete your own comments!")
                return redirect('/wall')

            else:
                insert_query =  "DELETE FROM comments WHERE id = :comment_id"
                query_data = {'comment_id': comment_id}
                mysql.query_db(insert_query, query_data)

                flash("The comment was deleted!")
                return redirect('/wall')

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
    session['email'] = user[0]['email']

    return redirect('/wall')

@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user(email)

        if len(user) != 0 and bcrypt.check_password_hash(user[0]['pw_hash'], password):
            print user
            session['id'] = user[0]['id']
            session['name'] = user[0]['first_name']
            session['email'] = user[0]['email']
            return redirect('/wall')

        else:
            flash("Please try again")
            return redirect('/login')

    elif request.method == 'GET':
        return render_template('login.html')

#logout user and clear session

@app.route('/logout', methods=['GET'])
def logout():

    if  'id' in session:
        session.pop('id')
        session.pop('name')
        session.pop('email')
        print session
        return redirect('/')

    else:
        flash("Already logged out")
        return redirect('/')

app.run(debug=True)
