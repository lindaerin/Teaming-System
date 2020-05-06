import random
import re
import string
from functools import wraps

import MySQLdb.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_mysqldb import MySQL

app = Flask(__name__)


mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'noreplywhiteboard001@gmail.com',
    "MAIL_PASSWORD": 'csc322spring',
    "MAIL_DEFAULT_SENDER": 'noreplywhiteboard001@gmail.com',
    "MAIL_SUPPRESS_SEND": False
}

app.config.update(mail_settings)
mail = Mail(app)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = '111'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Bang1adesh'
app.config['MYSQL_DB'] = 'csc322_project'

# Intialize MySQL
mysql = MySQL(app)


def login_required(func):  # login required decorato

    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrapper

def admin_login_required(func):  # login required decorato

    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id') and session.get('username') == 'admin':
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrapper


@app.route("/admin", methods=['get', 'post'])  # admin adding or deleting accounts
@admin_login_required #must be logged in as admin to access this page!
def admin():
    if request.method == 'POST':
        # add the account to the database
        if 'Approve' in request.form:
            #get data
            user_name = request.form['username']
            email = request.form['email']
            interest = request.form['interest']
            credential = request.form['credential']
            user_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            #check to see if accoutn already exist 
            cursor.execute('SELECT * FROM tb_user WHERE email = %s', (email,))
            account = cursor.fetchone()
            #if it doesnt insert into db 
            if not account:
                cursor.execute("INSERT INTO tb_user (user_name, user_password, email, credential, interest)"
                               " VALUES (%s, %s, %s, %s, %s)", (user_name, user_password, email, credential, interest))
                if request.form['message'] == "NONE":
                    welcome = user_name + " your Whiteboard application has been approved and your account has been created. Your temporary password is " + user_password + ". Use this link to reset your password : http://localhost:5000/reset_password"
                else: 
                    welcome = user_name + " your Whiteboard appeal has been approved and your account has been created. Your temporary password is " + user_password + " Use this link to reset your password : http://localhost:5000/reset_password"
                msg = Message("Welcome to Whiteboard!", recipients = [email])
                msg.body = welcome
                mail.send(msg)
            #delete from applied     
            cursor.execute("DELETE FROM tb_applied WHERE email = %s" , (email,))
            mysql.connection.commit()

        # reject the account
        elif 'Reject' in request.form:
            username = request.form['username']
            email = request.form['email']

            #send email
            if request.form['message'] == "NONE":
                reject = username + " we are sorry to say, your Whiteboard application has not been approved. Click on this link in order to appeal: http://localhost:5000/appeal"
            else:
                reject = username + " We are sorry to say, your Whiteboard appeal has not been approved"
                #put them into the blacklist 
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("INSERT INTO tb_blacklist (email)" "VALUES (%s)", (email,))
                mysql.connection.commit()
            msg = Message("Thank you for applying", recipients = [email])
            msg.body = reject
            mail.send(msg)

            #delete from tb applied 
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("DELETE FROM tb_applied WHERE email = %s", (email,))
            mysql.connection.commit()

    # load the admin page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tb_applied')
    # Fetch all post records and return result
    applied = cursor.fetchall()
    if applied:
        return render_template('admin.html', applied=applied)
    return render_template('admin.html')

#page where they can reset the password 
@app.route('/reset_password', methods=['POST', 'GET'])
def reset_password():
    msg = ''
    if request.method == "POST":
        #get information 
        email = request.form['email']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE email = %s and user_password = %s' , (email, old_password))
        account = cursor.fetchone()
        if not account:
            msg = "Unable to reset password"
            return render_template('reset_password.html',msg=msg)
        else:
            msg = "Success!"
            cursor.execute('UPDATE tb_user SET user_password = %s, didtheychangepass = %s WHERE user_id = %s' , (new_password, '1' , account['user_id']))
            mysql.connection.commit()
            return render_template('reset_password.html',msg=msg)
    return render_template('reset_password.html')

#appeal a rejection 
@app.route("/appeal", methods=['GET', 'POST'])  
def appeal():
    msg = ''
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        interest = request.form['interest']
        credential = request.form['credential']
        reference = request.form['reference']
        message = request.form['message']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE email = %s', (email,))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM tb_applied WHERE email = %s',(email,))
        applied = cursor.fetchone()

        if account or applied:
            msg = "You are already in the system - please check your email for a message from Whiteboard"
            return render_template("appeal.html", msg=msg)
        else:
            cursor.execute("INSERT INTO tb_applied (username, email, interest, credential, reference, message)"
                               " VALUES (%s, %s, %s, %s, %s, %s)", (username, email, interest, credential, reference, message))
            mysql.connection.commit()
            msg = "Your appeal will be shortly reviewed"
            return render_template('appeal.html', msg=msg)
    return render_template('appeal.html')


# this will be the home page, only accessible for loggedin users
@app.route("/")  # home page
def home():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # join table post and table user to get post_title, post_content, post_time, user_id, user_name
    cursor.execute('SELECT tb_post.*, tb_user.user_name FROM tb_post INNER JOIN tb_user ON'
                   ' tb_post.user_id = tb_user.user_id order by -post_time')
    # Fetch all post records and return result
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
    # join table reply and table user to get reply information
    cursor.execute('SELECT tb_reply.*, tb_user.user_name FROM tb_reply INNER JOIN tb_user ON '
                   'tb_user.user_id = tb_reply.user_id WHERE tb_reply.post_id = %s order by -reply_time', (post_id,))
    reply = cursor.fetchall()
    session['post_id'] = posted['post_id']
    return render_template('reply.html', posted=posted, reply=reply)


# reply feature
@app.route('/add_reply/', methods=['post'])
def add_reply():
    reply_content = request.form['reply_content']
    if not reply_content:
        flash('Please fill out the form!')
        return redirect(url_for('into_reply', post_id=session['post_id']))
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # insert data into table reply: user_id, reply_content, post_id
        cursor.execute('INSERT INTO tb_reply (user_id, reply_content, post_id) VALUES '
                       '(%s, %s, %s)', (session['user_id'], reply_content, session['post_id']))
        mysql.connection.commit()
        return redirect(url_for('into_reply', post_id=session['post_id']))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "email" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE email = %s AND user_password = %s', (email, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['user_id'] = account['user_id']
            session['username'] = account['user_name']
            if account['didtheychangepass'] == 0:
                return(redirect(url_for("reset_password")))
            else:
                # check if user is a new user
                cursor.execute('SELECT * FROM tb_profile WHERE user_id = %s', [session['user_id']])
                # if user is not a new user
                user_exist = cursor.fetchone()
                if user_exist:
                    # go profile page
                    return redirect(url_for('profile'))
                # otherwise insert data into table profile: user_id, user_type, user_status, user_scores
                cursor.execute('INSERT INTO tb_profile (user_id) VALUES (%s)', [session['user_id']])
                mysql.connection.commit()
                # go profile page
                return redirect(url_for('profile'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect email/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)


# this will be the registration page, we need to use both GET and POST requests
@app.route('/register/', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and other text feilds POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and \
            'email' in request.form and 'interest' in request.form and 'credential' in request.form and 'reference' in request.form:
        # Create variables for easy access
        username = request.form['username']  # get data from url
        email = request.form['email']
        interest = request.form['interest']
        credential = request.form['credential']
        reference = request.form['reference']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE email = %s', (email,))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM tb_applied WHERE email = %s', (email,))
        application = cursor.fetchone()
        # If account doesnt exists show error and validation checks
        if account or application:
            msg = 'Invalid Email!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z]+', username):
            msg = 'Username must contain only characters!'
        elif not re.match(r'[A-Za-z]+', interest):
            msg = 'Interest must contain only characters!'
        elif not re.match(r'[A-Za-z]+', credential):
            msg = 'Credential must contain only characters!'
        elif not re.match(r'[A-Za-z]+', reference):
            msg = 'Reference must contain only characters!'
        elif not username or not email or not credential or not reference or not interest:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into applied table
            cursor.execute("INSERT INTO tb_applied (username, email, interest, credential, reference)"
                           " VALUES (%s, %s, %s, %s, %s)", (username, email, interest, credential, reference))
            mysql.connection.commit()
            msg = 'You have successfully applied! Look for an email containing your username and password'
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
    if user_id:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE user_id = %s', (user_id,))
        # Fetch one record and return result
        account = cursor.fetchone()
        if account:
            return {'account': account}
    return {}


# this will be the profile page, only accessible for loggedin users
@app.route('/profile/myProfile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # join table profile and table user to get user information: id, name, email, user_type, user_scores,
        cursor.execute('SELECT tb_profile.*, tb_user.user_name, tb_user.email'
                       ' FROM tb_user INNER JOIN tb_profile ON tb_profile.user_id = tb_user.user_id'
                       ' WHERE tb_user.user_id = %s', [session['user_id']])
        account = cursor.fetchone()
        # get user post information
        cursor.execute('SELECT * FROM tb_post WHERE user_id = %s order by -post_time', [session['user_id']])
        # Fetch all records and return result
        post_history = cursor.fetchall()
        # get all the groups' information that the user
        cursor.execute('SELECT tb_group.*, tb_group_members.user_id FROM tb_group_members INNER JOIN tb_group'
                       ' ON tb_group.group_id = tb_group_members.group_id AND tb_group_members.user_id = %s',
                       [session['user_id']])
        group_info = cursor.fetchall()
        # Show the profile page with account info
        return render_template('profile.html', account=account, post_history=post_history, group_info=group_info)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# public user profile
@app.route('/user/<user_name>')
def public_profile(user_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # cursor.execute('SELECT * FROM tb_user WHERE user_name = %s', (user_name,))



    # join table user and table profile to get the poster information: id, name, email, user_type, user_scores
    cursor.execute('SELECT tb_profile.*, tb_user.user_name, tb_user.email, tb_user.user_id'
                   ' FROM tb_user INNER JOIN tb_profile ON'
                   ' tb_profile.user_id = tb_user.user_id WHERE tb_user.user_name = %s', (user_name,))
    account = cursor.fetchone()
    print(account)


    # if no username exists on file, return error
    if not account:
        flash("User doesn't exist")
        return redirect(url_for('404'))

    # get user's post history information: id, title, author, content, post_time and order by desc
    cursor.execute('SELECT tb_post.*, tb_user.user_id FROM tb_post INNER JOIN tb_user ON'
                       ' tb_post.user_id = tb_user.user_id WHERE tb_post.user_id = % s order by -post_time',
                       (account['user_id'],))
    post_history = cursor.fetchall()

    return render_template('profile.html', public_profile=account, post_history=post_history)

# this will be the poster_file page
@app.route('/poster_profile/<poster_id>')
def poster_profile(poster_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # join table user and table profile to get the poster information: id, name, email, user_type, user_scores
    cursor.execute('SELECT tb_profile.*, tb_user.user_name, tb_user.email, tb_user.user_id'
                   ' FROM tb_user INNER JOIN tb_profile ON'
                   ' tb_profile.user_id = tb_user.user_id WHERE tb_user.user_id = %s', (poster_id,))
    account = cursor.fetchone()
    if not account:
        flash("User doesn't exist")
        return redirect(url_for('home'))
    # if the user is the poster, it will into himself profile page directly
    elif account['user_id'] == session['user_id']:
        return redirect(url_for('profile'))
    # otherwise, it will into the this poster's profile page
    # get poster's post history information: id, title, author, content, post_time and order by desc
    cursor.execute('SELECT tb_post.*, tb_user.user_name FROM tb_post INNER JOIN tb_user ON'
                   ' tb_post.user_id = tb_user.user_id WHERE tb_post.user_id = % s order by -post_time', (poster_id,))
    post_history = cursor.fetchall()
    return render_template('profile.html', poster_account=account, post_history=post_history)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/logout/')
def logout():
    # Remove session data, this will log the user out
    session.pop('user_id', None)
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
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute("INSERT INTO tb_post (post_title, post_content, user_id)"
                           " VALUES (%s, %s, %s)", (title, content, session['user_id']))
            mysql.connection.commit()
            return redirect(url_for('home'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        # Show registration form with message (if any)
    return render_template('post.html', msg=msg)


# search bar
@app.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == "POST" and 'username' in request.form:
        username = request.form['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # search by username
        cursor.execute('SELECT * FROM tb_user WHERE user_name = %s', (username,))
        account = cursor.fetchone()
        if not account:
            flash('User does not exist')
            return redirect(url_for('home'))
        # if user search himself, it will into his profile page directly
        # elif account['user_name'] == session['username']:
        #     return redirect(url_for('profile'))
        else:
            # otherwise, go to the profile page of the searched user
            return redirect(url_for('public_profile', user_name=account['user_name']))


# create a group
# @app.route('/group/', methods=['GET', 'POST'])
# # def create_group():
# #     if request.method == "POST":
# #         group_name = request.form['group_name']
# #         group_describe = request.form['describe']
# #         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
# #         # check if the group name entered by the user was in the table group
# #         cursor.execute('SELECT * FROM tb_group WHERE group_name = %s', (group_name,))
# #         group_name_exist = cursor.fetchone()
# #         # if exist: show the error message and return to the profile page
# #         if group_name_exist:
# #             flash('Group Already Exist')
# #             return redirect(url_for('profile'))
# #         # otherwise insert data into table group: group_name, user_id, group_describe
# #         cursor.execute('INSERT INTO tb_group (group_name, user_id, group_describe) VALUES (%s, %s, %s)',
# #                        (group_name, session['user_id'], group_describe))
# #         mysql.connection.commit()
# #         # get the group id by desc
# #         cursor.execute('SELECT group_id FROM tb_group order by -group_id')
# #         group_id = cursor.fetchone()
# #         # insert data into table group_members: group_id and user_name
# #         cursor.execute('INSERT INTO tb_group_members (group_id, user_name) VALUES (%s, %s)',
# #                        (group_id['group_id'], session['username']))
# #         mysql.connection.commit()
# #         return redirect(url_for('profile'))

@app.route('/group/', methods=['GET', 'POST'])
def create_group():
    msg = ''
    # if request.method == 'POST' and 'team_name' in request.form and 'invite' in request.form:
    if request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Create variables for easy access
        group_name = request.form['group_name']
        invite = request.form['invite']
        description = request.form['description']

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

        if not group_name:
            msg='Please enter a group name'
            return render_template('group.html', msg=msg, group_name=group_name, invite=invite, description=description)

        if not invite:
            msg = 'Please invite users to group'
            return render_template('group.html', msg=msg, group_name=group_name, invite=invite, description=description)

        if not invite and not group_name:
            msg = 'Please fill out the form'
            return render_template('group.html', msg=msg)

        # cursor.execute('SELECT user_id from tb_user WHERE user_name = %s', (invite,))
        # invite_id = cursor.fetchone()
        # invite_id_final = invite_id['user_id']

        # Check if team_name exists in tb_group table
        cursor.execute('SELECT * FROM tb_group WHERE group_name = %s', (group_name,))
        name = cursor.fetchone()

        # If team_name currently exists, show error that it is taken
        if name:
            msg = 'This Project Name is already taken!'
            return render_template('group.html', msg=msg, group_name=group_name, invite=invite, description=description)
        else:
            msg = 'You have successfully created a team!'
            # Insert project name to make project id into tb_group
            cursor.execute("INSERT INTO tb_group (group_name, group_describe)"
                           " VALUES (%s, %s)", (group_name, description,))
            # Get newly created group_id
            cursor.execute('SELECT group_id FROM tb_group WHERE group_name = %s', (group_name,))
            new_team = cursor.fetchone()
            new_team_val = new_team['group_id']

            # Run Stored Procedure to run on invited members and add to tb_group_members
            cursor.callproc('insert_members', [group_members, new_team_val])

            # Save new data into database
            mysql.connection.commit()
            # session['group_members'] = invite

            return redirect(url_for('group_page', group_name=group_name))

    return render_template('group.html')




@app.route('/group/<group_name>', methods=['GET', 'POST'])
def group_page(group_name):
    # check if group name exists within database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT group_name from tb_group WHERE group_name = %s', (group_name,))
    groupExists = cursor.fetchone()
    # app.logger.info(groupExists)

    if groupExists:
        # get group_id
        cursor.execute('SELECT * from tb_group WHERE group_name = %s', (group_name,))
        group = cursor.fetchone()
        group_id = group['group_id']

        # get list of users from table and save it as a string
        # INNER JOIN HERE
        cursor.execute('SELECT user_name from tb_user inner join tb_group_members ON tb_user.user_id = tb_group_members.user_id WHERE group_id = %s', (group_id,))
        usernames = cursor.fetchall()

        final_usernames = usernames[0]['user_name']

        # loop through each usernames tuple and add them to final_usernames string
        for i in range(1, len(usernames)):
            current_user = usernames[i]['user_name']
            final_usernames = final_usernames + ", " + current_user

        print(final_usernames)

        # get group description
        cursor.execute('SELECT group_describe from tb_group WHERE group_name = %s', (group_name,))
        desc = cursor.fetchone()
        team_desc = desc['group_describe']

        print(group)

        return render_template('group_page.html', group=group, members=final_usernames, description=team_desc)
    else:
        return render_template('404.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')



# invite feature
@app.route("/invite/<group_id>", methods=['POST'])
def invite(group_id):
    if request.method == 'POST':
        user_name = request.form['user_name']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # check the user name the user inputted if exist in user database
        cursor.execute('SELECT user_name FROM tb_user WHERE user_name = %s', (user_name,))
        user_name_exist = cursor.fetchone()
        # if not exist, output error message, then return to the group page
        if not user_name_exist:
            flash("User doesn't exist")
            return redirect(url_for('group_page', group_id=group_id))
        # otherwise, check the username if exist in this group
        cursor.execute('SELECT tb_group_members.* FROM tb_group_members INNER JOIN tb_user ON '
                       'tb_group_members.user_name = tb_user.user_name'
                       ' WHERE tb_user.user_name = %s AND tb_group_members.group_id = %s', (user_name, group_id))
        group_member = cursor.fetchall()
        # if this user already in this group, show the error message
        if group_member:
            flash('This User Already in this Group')
            return redirect(url_for('group_page', group_id=group_id))
        # otherwise, insert data into table group_members
        cursor.execute('INSERT INTO tb_group_members (group_id, user_name) VALUES (%s, %s)', (group_id, user_name))
        mysql.connection.commit()
        return redirect(url_for('group_page', group_id=group_id))


if __name__ == '__main__':
    app.run(debug=True)