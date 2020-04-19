from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import logging
import MySQLdb.cursors
import re
from functools import wraps

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = '111'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
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
    cursor.execute('SELECT post_title, post_content, post_time, user_name, post_id, user_id'
                   ' FROM tb_post order by -post_time')
    # Fetch all records and return result
    post = cursor.fetchall()
    if post:
        return render_template('index.html', post=post)
    return render_template('index.html')


#  link the post_content to the reply page
@app.route('/reply/<post_id>/')
@login_required
def into_reply(post_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tb_post WHERE post_id = %s', (post_id,))
    posted = cursor.fetchone()
    cursor.execute('SELECT reply_content, reply_time, user_name, user_id, post_id'
                   ' FROM tb_reply WHERE post_id = %s order by -reply_time', (post_id,))
    reply = cursor.fetchall()
    session['post_id'] = posted['post_id']
    return render_template('reply.html', posted=posted, reply=reply)


# reply feature
@app.route('/add_reply/', methods=['post'])
def add_reply():
    reply_content = request.form['reply_content']
    if not reply_content:
        return redirect(url_for('into_reply', post_id=session['post_id']))
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO tb_reply (user_name, user_id, reply_content, post_id) VALUES '
                       '(%s, %s, %s, %s)', (session['username'], session['user_id'], reply_content, session['post_id']))
        mysql.connection.commit()
        return redirect(url_for('into_reply', post_id=session['post_id']))


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


# display current user on navigation bar
@app.context_processor
def my_context_processor():
    user_id = session.get('user_id')
    print('user_id', user_id)
    if user_id:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE user_id = %s', (user_id,))
        # Fetch one record and return result
        account = cursor.fetchone()
        if account:
            return {'account': account}
    return {}


# http://localhost:5000/pythinlogin/profile - this will be the profile page, only accessible for loggedin users
@app.route('/profile/myProfile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE user_id = %s', [session['user_id']])
        account = cursor.fetchone()

        # Get All group info of user if there exists any
        cursor.execute('select team_name, team_content from tb_team inner join group_members on tb_team.team_id = group_members.group_id where user_id = %s', ([session['user_id']],))
        group_info = cursor.fetchall()


        # if user doesn't have a team
        if group_info is None or group_info == ():
            group_info = []

        # if user belongs in more one team or more
        if len(group_info) >= 1:
            temp = []

            # loop through each team_name tuple and add them into final team_name string
            for i in range(0, len(group_info)):
                temp.append(group_info[i]['team_name'])

            group_info = temp

        # Get all post history of user if there exists any
        cursor.execute('SELECT post_title, post_content, post_time, user_name, post_id, user_id'
                       ' FROM tb_post WHERE user_id = %s order by -post_time', [session['user_id']])
        # Fetch all records and return result
        posts = cursor.fetchall()


        # Show the profile page with account info
        return render_template('profile.html', account=account, posts=posts, group_info=group_info)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# this will be the poster_file page
@app.route('/poster_profile/<poster_id>')
@login_required
def poster_profile(poster_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tb_user WHERE user_id = %s', (poster_id,))
    account = cursor.fetchone()
    return render_template('profile.html', poster_account=account)

# search bar
@app.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == "POST" and 'username' in request.form:
        username = request.form['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # search by username
        cursor.execute('SELECT * FROM tb_user WHERE user_name = %s', (username,))
        account = cursor.fetchone()
        print(account)
        if not account:
            flash('User does not exist')
            return render_template('404.html')
        elif account['user_name'] == session['username']:
            return redirect(url_for('profile'))
        else:
            return redirect(url_for('public_profile', user_name=account['user_name']))

# public user profile
@app.route('/public/user/<user_name>')
def public_profile(user_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tb_user WHERE user_name = %s', (user_name,))
    account = cursor.fetchone()
    return render_template('profile.html', public_profile=account)




# http://localhost:5000/python/logout - this will be the logout page
@app.route('/logout/')
def logout():
    # Remove session data, this will log the user out
    # session.pop('loggedin', None)
    session.pop('user_id', None)
    # session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/post/', methods=['GET', 'POST'])
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
            mysql.connection.commit()
            return redirect(url_for('home'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        # Show registration form with message (if any)
    return render_template('post.html', msg=msg)


@app.route('/create-group/', methods=['GET', 'POST'])
@login_required
def create_group():
    msg = ''
    # if request.method == 'POST' and 'team_name' in request.form and 'invite' in request.form:
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Create variables for easy access
        team_name = request.form['team_name']
        invite = request.form['invite']
        team_desc = request.form['content']

        # convert team member user_names into string of user_id to pass into stored procedure
        # add session['user_id']
        group_members = str(session['user_id'])

        new_invite = invite.split(",")

        # take array of split user_names and convert into user_id string
        for i in range(0, len(new_invite)):
            cursor.execute('SELECT user_id from tb_user WHERE user_name = %s', (new_invite[i],))
            current = cursor.fetchone()
            current_user = current['user_id']
            group_members = group_members + "," + str(current_user)

        if not team_name:
            msg='Please enter a group name'
            return render_template('create_group.html', msg=msg, team_name=team_name, invite=invite, content=team_desc)

        if not invite:
            msg = 'Please invite users to group'
            return render_template('create_group.html', msg=msg, team_name=team_name, invite=invite, content=team_desc)

        if not invite and not team_name:
            msg = 'Please fill out the form'
            return render_template('create_group.html', msg=msg)

        # cursor.execute('SELECT user_id from tb_user WHERE user_name = %s', (invite,))
        # invite_id = cursor.fetchone()
        # invite_id_final = invite_id['user_id']

        # Check if team_name exists in tb_team table
        cursor.execute('SELECT * FROM tb_team WHERE team_name = %s', (team_name,))
        name = cursor.fetchone()

        # If team_name currently exists, show error that it is taken
        if name:
            msg = 'This Project Name is already taken!'
            return render_template('create_group.html', msg=msg, team_name=team_name, invite=invite, content=team_desc)
        else:
            msg = 'You have successfully created a team!'
            # Insert project name to make project id into tb_team
            cursor.execute("INSERT INTO tb_team (team_name, team_content)"
                           " VALUES (%s, %s)", (team_name, team_desc,))
            # Get newly created group_id
            cursor.execute('SELECT team_id FROM tb_team WHERE team_name = %s', (team_name,))
            new_team = cursor.fetchone()
            new_team_val = new_team['team_id']

            # Run Stored Procedure to run on invited members and add to group_members
            cursor.callproc('insert_members', [group_members, new_team_val])

            # Save new data into database
            mysql.connection.commit()
            # session['group_members'] = invite

            return redirect(url_for('group_page', group_name=team_name))

    return render_template('create_group.html')


@app.route('/group/<group_name>', methods=['GET', 'POST'])
def group_page(group_name):
    # check if group name exists within database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT team_name from tb_team WHERE team_name = %s', (group_name,))
    groupExists = cursor.fetchone()
    # app.logger.info(groupExists)

    if groupExists:
        # get group_id
        cursor.execute('SELECT team_id from tb_team WHERE team_name = %s', (group_name,))
        group = cursor.fetchone()
        group_id = group['team_id']

        # get list of users from table and save it as a string
        # INNER JOIN HERE
        cursor.execute('SELECT user_name from tb_user inner join group_members ON tb_user.user_id = group_members.user_id WHERE group_id = %s', (group_id,))
        usernames = cursor.fetchall()

        final_usernames = usernames[0]['user_name']

        # loop through each usernames tuple and add them to final_usernames string
        for i in range(1, len(usernames)):
            current_user = usernames[i]['user_name']
            final_usernames = final_usernames + ", " + current_user

        print(final_usernames)

        # get group description
        cursor.execute('SELECT team_content from tb_team WHERE team_name = %s', (group_name,))
        desc = cursor.fetchone()
        team_desc = desc['team_content']

        return render_template('group_page.html', group_name = group_name, team_desc = team_desc, members=final_usernames)
    else:
        return render_template('404.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')


if __name__ == '__main__':
    app.run(debug=True)
