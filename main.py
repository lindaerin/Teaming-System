from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from functools import wraps

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = '111'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '111111'
app.config['MYSQL_DB'] = 'csc322_project'

# Intialize MySQL
mysql = MySQL(app)


def login_required(func):  # login required decorator

    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrapper


# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route("/")  # home page
def home():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT post_title, post_content, post_time, user_name FROM tb_post order by'
                       ' -post_time')
        # Fetch all records and return result
        post = cursor.fetchall()
        print('post', post)
        if post:
            return render_template('index.html', post=post)
        return render_template('index.html')




@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE user_name = %s AND user_password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['user_id'] = account['user_id']
            session['username'] = account['user_name']
            # session['password'] = account['user_password']
            # Redirect to home page
            return redirect(url_for('profile'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register/', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and \
            'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']  # get data from url
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE user_name = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute("INSERT INTO tb_user (user_name, user_password, email)"
                           " VALUES (%s, %s, %s)", (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return render_template('login.html', msg=msg)
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


@app.context_processor
def my_context_processor():
    user_id = session.get('user_id')
    if user_id:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE user_id = %s', (user_id,))
        # Fetch one record and return result
        account = cursor.fetchone()
        if account:
            return {'account': account}
    return {}


# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile/')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE user_id = %s', [session['user_id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/logout/')
def logout():
    # Remove session data, this will log the user out
    # session.pop('loggedin', None)
    session.pop('user_id', None)
    # session.pop('username', None)

    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/profile/post', methods=['GET', 'POST'])
@login_required
def post():
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'title' in request.form and 'content' in request.form:
        # Create variables for easy access
        title = request.form['title']  # get data from url form
        content = request.form['content']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_post WHERE post_title = %s', (title,))
        post = cursor.fetchone()
        # If account exists show error and validation checks
        if post:
            msg = 'Error: Title already exists!\n'
        elif not title or not content:
            msg = 'Error: Please fill out the form!\n'
        else:
            msg = 'You have successfully posted!'
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute("INSERT INTO tb_post (post_title, post_content, user_id, user_name)"
                           " VALUES (%s, %s, %s, %s)", (title, content, session['user_id'], session['username']))
            post = cursor.fetchall()

            mysql.connection.commit()

            return render_template('index.html', post=post)
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        # Show registration form with message (if any)
    return render_template('post.html', msg=msg)


if __name__ == '__main__':
    app.run(debug=True)