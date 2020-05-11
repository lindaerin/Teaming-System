import random
import re
import string
from functools import wraps

import MySQLdb.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_mysqldb import MySQL

app = Flask(__name__)

# email configurations
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

# creates the mail feature
app.config.update(mail_settings)
mail = Mail(app)

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


def admin_login_required(func):  # admin login required decorator

    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id') and session.get('username') == 'admin':
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrapper


@app.route("/admin", methods=['get', 'post'])  # admin adding or deleting accounts
@admin_login_required  # must be logged in as admin to access this page!
def admin():
    if request.method == 'POST':
        # add the account to the database
        if 'Approve' in request.form:
            # get data
            user_name = request.form['username']
            email = request.form['email']
            interest = request.form['interest']
            credential = request.form['credential']
            user_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # check to see if account already exist by email or user_name
            cursor.execute('SELECT * FROM tb_user WHERE email = %s OR user_name = %s', (email, user_name))
            account = cursor.fetchone()
            # if it doesnt insert into db
            if not account:
                cursor.execute("INSERT INTO tb_user (user_name, user_password, email, credential, interest)"
                               " VALUES (%s, %s, %s, %s, %s)", (user_name, user_password, email, credential, interest))
                # send email depending if it is an appeal or first time application
                if request.form['message'] == "NONE":
                    welcome = user_name + " your Whiteboard application has been approved and your account has been" \
                                          " created. Your temporary password is " + user_password + ". Use" \
                                                                                                    " this link to reset your password : http://localhost:5000/reset_password"
                else:
                    welcome = user_name + " your Whiteboard appeal has been approved and your account has" \
                                          " been created. Your temporary password is " + user_password + " Use" \
                                                                                                         " this link to reset your password : http://localhost:5000/reset_password"
                msg = Message("Welcome to Whiteboard!", recipients=[email])
                msg.body = welcome
                mail.send(msg)
            # delete from applied
            cursor.execute("DELETE FROM tb_applied WHERE email = %s", (email,))
            mysql.connection.commit()

        # reject the account
        elif 'Reject' in request.form:
            username = request.form['username']
            email = request.form['email']

            # send email depending if it appeal or first time applications
            if request.form['message'] == "NONE":
                reject = username + " we are sorry to say, your Whiteboard application has not been approved." \
                                    " Click on this link in order to appeal: http://localhost:5000/appeal"
            else:
                reject = username + " We are sorry to say, your Whiteboard appeal has not been approved"
                # put them into the blacklist if it is an appeal
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("INSERT INTO tb_blacklist (email)" "VALUES (%s)", (email,))
                mysql.connection.commit()
            msg = Message("Thank you for applying", recipients=[email])
            msg.body = reject
            mail.send(msg)

            # delete from tb applied
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


# page where they can reset the password
@app.route('/reset_password', methods=['POST', 'GET'])
def reset_password():
    msg = ''
    if request.method == "POST":
        # get information
        email = request.form['email']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # check to see if the account exists and the information is correct
        cursor.execute('SELECT * FROM tb_user WHERE email = %s and user_password = %s', (email, old_password))
        account = cursor.fetchone()
        if not account:
            msg = "Unable to reset password"
            return render_template('reset_password.html', msg=msg)
        # if the info is correct than change password and indicate they have changed their password
        else:
            msg = "Success!"
            cursor.execute('UPDATE tb_user SET user_password = %s, didtheychangepass = %s WHERE user_id = %s',
                           (new_password, '1', account['user_id']))
            mysql.connection.commit()
            return render_template('reset_password.html', msg=msg)
    return render_template('reset_password.html')


# appeal a rejection
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
        # check to see if the email is already in the db
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tb_user WHERE email = %s OR user_name = %s', (email, username))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM tb_applied WHERE email = %s OR username = %s', (email, username))
        applied = cursor.fetchone()
        # if email is in the system they cannot appeal
        if account or applied:
            msg = "You are already in the system - please check your email for a message from Whiteboard" \
                  " or try a different username"
            return render_template("appeal.html", msg=msg)
        else:
            cursor.execute("INSERT INTO tb_applied (username, email, interest, credential, reference, message)"
                           " VALUES (%s, %s, %s, %s, %s, %s)",
                           (username, email, interest, credential, reference, message))
            mysql.connection.commit()
            msg = "Your appeal will be shortly reviewed"
            return render_template('appeal.html', msg=msg)
    return render_template('appeal.html')


# this will be the home page, only accessible for loggedin users
@app.route("/")  # home page
def home():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # join table post and table user to get post_title, post_content, post_time, user_id, user_name
    cursor.execute('SELECT tb_post.*, tb_user.user_name, tb_profile.user_type FROM tb_post INNER JOIN tb_user ON'
                   ' tb_post.user_id = tb_user.user_id INNER JOIN tb_profile ON tb_profile.user_id = tb_post.user_id'
                   ' order by -post_time')
    # Fetch all post records and return result
    post = cursor.fetchall()
    # count replied number for each post
    for i in range(len(post)):
        cursor.execute('SELECT COUNT(post_id) FROM tb_reply WHERE post_id =%s', [post[i]['post_id']])
        count = cursor.fetchone()
        post[i]['replied_num'] = count.get('COUNT(post_id)')
    # sorted by the replied number to determine which post has the most replies
    post = sorted(post, key=lambda post: (post['replied_num']), reverse=True)
    # flag general post, since we need to show the top 3 rated post, we add the flag at the 4th post
    if len(post) > 3:
        post[3]['flag'] = 1
    # Select all ordinary user profiles and sort by scores
    cursor.execute('SELECT tb_user.*, tb_profile.user_type, tb_profile.user_scores FROM tb_user INNER JOIN tb_profile '
                   'ON tb_user.user_id = tb_profile.user_id WHERE tb_profile.user_type = "Ordinary" order by '
                   '-tb_profile.user_scores ')
    top_OU = cursor.fetchall()
    # if exist ordinary user profiles
    if top_OU:
        # if total ordinary users < 3, only show their profiles
        if len(top_OU) < 3:
            top_OU = top_OU[:len(top_OU)]
        # otherwise, show the top 3 rated ordinary users' profiles
        else:
            top_OU = top_OU[:3]
    # Select all super user profiles and sort by scores
    cursor.execute('SELECT tb_user.*, tb_profile.user_type, tb_profile.user_scores FROM tb_user INNER JOIN tb_profile '
                   'ON tb_user.user_id = tb_profile.user_id WHERE tb_profile.user_type = "SuperUser" order by '
                   '-tb_profile.user_scores ')
    top_SU = cursor.fetchall()
    # if exist super user profiles
    if top_SU:
        # if total super users < 3, only show their profiles
        if len(top_SU) < 3:
            top_SU = top_SU[:len(top_SU)]
        # otherwise, show the top 3 rated super users' profiles
        else:
            top_SU = top_SU[:3]

    if post:
        return render_template('index.html', post=post, top_SU=top_SU, top_OU=top_OU)

    return render_template('index.html', top_SU=top_SU, top_OU=top_OU)


#  link the post_content to the reply page
@app.route('/reply/<post_id>/')
@login_required
def into_reply(post_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT tb_post.*, tb_user.user_name FROM tb_post INNER JOIN tb_user ON'
                   ' tb_post.user_id = tb_user.user_id WHERE tb_post.post_id = %s', (post_id,))
    posted = cursor.fetchone()
    # join table reply and table user to get reply information
    cursor.execute('SELECT tb_reply.*, tb_user.user_name FROM tb_reply INNER JOIN tb_user ON '
                   'tb_user.user_id = tb_reply.user_id WHERE tb_reply.post_id = %s order by -reply_time', (post_id,))
    reply = cursor.fetchall()
    # declare the reply_number
    reply_number = len(reply)
    session['post_id'] = posted['post_id']
    return render_template('reply.html', posted=posted, reply=reply, reply_number=reply_number)


# reply feature
@app.route('/add_reply/', methods=['post'])
def add_reply():
    if request.method == 'POST':
        reply_content = request.form['reply_content']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Find the current user information
        cursor.execute('SELECT * FROM tb_profile WHERE tb_profile.user_id = %s', [session['user_id']], )
        user_info = cursor.fetchone()
        # if the user_type is Ordinary
        if user_info['user_type'] == 'Ordinary':
            # Check out the taboo word list
            cursor.execute('SELECT * FROM tb_taboo')
            taboo_list = cursor.fetchall()
            # Create a list to save all taboo words the user typed in the post
            taboo_words = []
            for i in range(len(taboo_list)):
                # find all taboo words in the user post_content, ignore all cases
                taboo = re.findall(taboo_list[i]['word'], reply_content, flags=re.IGNORECASE)
                # if exist
                if taboo:
                    # remove repeat taboo words
                    taboo = list(dict.fromkeys(taboo))
                    # add into the list
                    taboo_words += taboo
                    for j in range(len(taboo)):
                        # replace the taboo words to be ***
                        reply_content = reply_content.replace(taboo[j], '***')
            # make all taboo words to be lower case
            taboo_words = [x.lower() for x in taboo_words]
            # remove the repeat taboo words
            taboo_words = list(dict.fromkeys(taboo_words))
            # if taboo_words exist:
            if taboo_words:
                cursor.execute('UPDATE tb_profile SET user_scores = %s WHERE user_id = %s',
                               ((user_info['user_scores'] - 1), session['user_id']))
                mysql.connection.commit()
                flash('Warning! Your Chat contains taboo words, Your Reputation will be reduced by this Rule:'
                      ' First Time use this word : -1 point, Next Time: -5 points ')

                for i in range(len(taboo_words)):
                    # insert taboo words into table user_taboo
                    cursor.execute('INSERT INTO tb_user_taboo (user_id, word) VALUES (%s, %s)',
                                   (session['user_id'], taboo_words[i]))
                    mysql.connection.commit()

                    # find all information of this user in table user_taboo
                    cursor.execute('SELECT * FROM tb_user_taboo WHERE user_id = %s AND word = %s',
                                   (session['user_id'], taboo_words[i]))
                    user_taboo = cursor.fetchall()
                    print(user_taboo)
                    # if this word occurs > 1, scores - 5
                    if len(user_taboo) > 1:
                        cursor.execute('UPDATE tb_profile SET user_scores = %s WHERE user_id = %s',
                                       ((user_info['user_scores'] - 5), session['user_id']))
                        mysql.connection.commit()

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
            # check if user is a new user
            cursor.execute('SELECT * FROM tb_profile WHERE user_id = %s', [session['user_id']])
            # if user is not a new user
            user_exist = cursor.fetchone()
            if user_exist:
                # go profile page
                if account['didtheychangepass'] == 0:
                    return (redirect(url_for("reset_password")))
                else:
                    return redirect(url_for('profile'))
            # otherwise insert data into table profile: user_id, user_type, user_status, user_scores
            cursor.execute('INSERT INTO tb_profile (user_id) VALUES (%s)', [session['user_id']])
            mysql.connection.commit()
            # go profile page
            if account['didtheychangepass'] == 0:
                return redirect(url_for("reset_password"))
            else:
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
    # Check if "username", "password" and other text fields POST requests exist (user submitted form)
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
        cursor.execute('SELECT * FROM tb_user WHERE email = %s OR user_name = %s', (email, username))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM tb_applied WHERE email = %s OR username = %s', (email, username))
        application = cursor.fetchone()
        # If account doesnt exists show error and validation checks
        if account or application:
            msg = 'Invalid Email or Username!'
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
@app.route('/profile/myProfile', methods=['POST', 'GET'])
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == "POST":

            # is user approved a group invitations
            if 'Approve' in request.form:
                group_id = request.form['group_id']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                # insert them into the group, insert a message into the group chat, and delete the group from invites
                cursor.execute('INSERT INTO tb_group_members (group_id, user_name) VALUES (%s, %s)',
                               (group_id, [session['username']]))
                cursor.execute('INSERT INTO tb_chat (user_id, group_id, chat_content) VALUES (%s, %s, %s)',
                               ([session['user_id']], group_id, "Has joined the group!"))
                cursor.execute('DELETE from tb_invite WHERE user_id = %s AND group_id = %s',
                               ([session['user_id']], group_id))
                mysql.connection.commit()

            # if user reject an invite
            elif 'Reject' in request.form:
                rejection = request.form['rejection']
                message = "Thank you for the consideration, but I will not accept invitation to this group." \
                          " I cannot join this group, " + rejection
                group_id = request.form['group_id']
                # insert the rejection message into group chat and delete the invitation
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO tb_chat (user_id, group_id, chat_content) VALUES (%s, %s, %s)',
                               ([session['user_id']], group_id, message))
                cursor.execute('DELETE from tb_invite WHERE user_id = %s AND group_id = %s',
                               ([session['user_id']], group_id))
                mysql.connection.commit()

            # if user is adding a user to their whitelist
            elif "whitelist" in request.form:
                user_whitelist = request.form['user_whitelist']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                # check the user name the user inputted if exist in user database
                cursor.execute('SELECT user_name FROM tb_user WHERE user_name = %s', (user_whitelist,))
                user_name_exist = cursor.fetchone()
                # if not exist, output error message, then return to the group page
                if not user_name_exist:
                    flash("User doesn't exist")
                else:
                    # else check if the user is already in their whitelist or blacklist
                    cursor.execute('SELECT * FROM tb_whitelist WHERE user_id = %s AND user_name_friend = %s',
                                   ([session['user_id']], user_whitelist))
                    exist = cursor.fetchone()
                    cursor.execute('SELECT * FROM tb_user_blacklist WHERE user_id = %s AND user_name_blocked = %s',
                                   ([session['user_id']], user_whitelist))
                    otherlist = cursor.fetchone()
                    # if not then insert it into the correct list
                    if not exist and not otherlist:
                        cursor.execute("INSERT INTO tb_whitelist (user_id, user_name_friend)" "VALUES (%s,%s)",
                                       ([session['user_id']], user_whitelist))
                        mysql.connection.commit()

            # user adding into the black list
            elif "blacklist" in request.form:
                user_blacklist = request.form['user_blacklist']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                # check the user name the user inputted if exist in user database
                cursor.execute('SELECT user_name FROM tb_user WHERE user_name = %s', (user_blacklist,))
                user_name_exist = cursor.fetchone()
                # if not exist, output error message, then return to the group page
                if not user_name_exist:
                    flash("User doesn't exist")
                else:
                    # check if the user already exist in either of list
                    cursor.execute('SELECT * FROM tb_user_blacklist WHERE user_id = %s AND user_name_blocked = %s',
                                   ([session['user_id']], user_blacklist))
                    exist = cursor.fetchone()
                    cursor.execute('SELECT * FROM tb_whitelist WHERE user_id = %s AND user_name_friend = %s',
                                   ([session['user_id']], user_blacklist))
                    otherlist = cursor.fetchone()
                    # if not put them into the list
                    if not exist and not otherlist:
                        cursor.execute("INSERT INTO tb_user_blacklist (user_id, user_name_blocked)" "VALUES (%s,%s)",
                                       ([session['user_id']], user_blacklist))
                        mysql.connection.commit()
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
        cursor.execute('SELECT tb_group.*, tb_group_members.user_name FROM tb_group_members INNER JOIN tb_group'
                       ' ON tb_group.group_id = tb_group_members.group_id AND tb_group_members.user_name = %s',
                       [session['username']])
        group_info = cursor.fetchall()
        # have to join with the group tablle
        cursor.execute('SELECT tb_invite.*, tb_group.group_name, tb_group.group_describe FROM tb_group INNER JOIN '
                       'tb_invite ON tb_invite.group_id = tb_group.group_id WHERE tb_invite.user_id = %s',
                       [session['user_id']])
        invitation = cursor.fetchall()
        # get black and whitelist informations
        cursor.execute('SELECT user_name_friend FROM tb_whitelist WHERE user_id = %s', [session['user_id']])
        friends = cursor.fetchall()
        cursor.execute('SELECT user_name_blocked FROM tb_user_blacklist WHERE user_id = %s', [session['user_id']])
        blocked = cursor.fetchall()
        # Show the profile page with account info
        return render_template('profile.html', account=account, post_history=post_history, group_info=group_info,
                               invitation=invitation, friends=friends, blocked=blocked)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# this will be the poster_file page
@app.route('/poster_profile/<poster_id>')
# @login_required
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
    elif account['user_id'] == session.get('user_id'):
        return redirect(url_for('profile'))
    # otherwise, it will into the this poster's profile page
    # get poster's post history information: id, title, author, content, post_time and order by desc
    cursor.execute('SELECT tb_post.*, tb_user.user_name FROM tb_post INNER JOIN tb_user ON'
                   ' tb_post.user_id = tb_user.user_id WHERE tb_post.user_id = % s order by -post_time', (poster_id,))
    post_history = cursor.fetchall()
    cursor.execute('SELECT tb_group.group_id, tb_group.group_name FROM tb_group_members INNER JOIN tb_group ON'
                   ' tb_group.group_id = tb_group_members.group_id INNER JOIN tb_user ON'
                   ' tb_group_members.user_name = tb_user.user_name WHERE tb_user.user_id = %s', (poster_id,))

    others_group_info = cursor.fetchall()
    return render_template('profile.html', poster_account=account, post_history=post_history,
                           others_group_info=others_group_info)


# this will be the logout page
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
        title_exist = cursor.fetchone()
        # If account exists show error and validation checks
        if title_exist:
            msg = 'Error: Title already exists!\n'
        else:
            # Find the current user information
            cursor.execute('SELECT * FROM tb_profile WHERE tb_profile.user_id = %s', [session['user_id']], )
            user_info = cursor.fetchone()
            # if the user_type is Ordinary
            if user_info['user_type'] == 'Ordinary':
                # Check out the taboo word list
                cursor.execute('SELECT * FROM tb_taboo')
                taboo_list = cursor.fetchall()
                # Create a list to save all taboo words the user typed in the post
                taboo_words = []
                for i in range(len(taboo_list)):
                    # find all taboo words in the user post_content, ignore all cases
                    taboo = re.findall(taboo_list[i]['word'], content, flags=re.IGNORECASE)
                    # if exist
                    if taboo:
                        # remove repeat taboo words
                        taboo = list(dict.fromkeys(taboo))
                        # add into the list
                        taboo_words += taboo
                        for j in range(len(taboo)):
                            # replace the taboo words to be ***
                            content = content.replace(taboo[j], '***')
                # make all taboo words to be lower case
                taboo_words = [x.lower() for x in taboo_words]
                # remove the repeat taboo words
                taboo_words = list(dict.fromkeys(taboo_words))
                if taboo_words:
                    cursor.execute('UPDATE tb_profile SET user_scores = %s WHERE user_id = %s',
                                   ((user_info['user_scores'] - 1), session['user_id']))
                    mysql.connection.commit()
                    flash('Warning! Your Post contains taboo words, Your Reputation will be reduced by this Rule:'
                          ' First Time use this word : -1 point, Next Time: -5 points ')

                    for i in range(len(taboo_words)):
                        # insert taboo words into table user_taboo
                        cursor.execute('INSERT INTO tb_user_taboo (user_id, word) VALUES (%s, %s)',
                                       (session['user_id'], taboo_words[i]))
                        mysql.connection.commit()

                        # find all information of this user in table user_taboo
                        cursor.execute('SELECT * FROM tb_user_taboo WHERE user_id = %s AND word = %s',
                                       (session['user_id'], taboo_words[i]))
                        user_taboo = cursor.fetchall()
                        print(user_taboo)
                        # if this word occurs > 1, scores - 5
                        if len(user_taboo) > 1:
                            cursor.execute('UPDATE tb_profile SET user_scores = %s WHERE user_id = %s',
                                           ((user_info['user_scores'] - 5), session['user_id']))
                            mysql.connection.commit()

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


# delete post
@app.route('/<post_id>/')
def delete_post(post_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    print('p_id', post_id)
    cursor.execute('DELETE FROM tb_post WHERE post_id = %s', (post_id,))
    mysql.connection.commit()
    return redirect(url_for('profile'))




# search bar
@app.route('/search/', methods=['GET', 'POST'])
@login_required
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
        elif account['user_name'] == session['username']:
            return redirect(url_for('profile'))
        else:
            # otherwise, go to the profile page of the searched user
            return redirect(url_for('poster_profile', poster_id=account['user_id']))


# create a group
@app.route('/group/', methods=['GET', 'POST'])
def create_group():
    if request.method == "POST":
        group_name = request.form['group_name']
        group_describe = request.form['describe']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # check if the group name entered by the user was in the table group
        cursor.execute('SELECT * FROM tb_group WHERE group_name = %s', (group_name,))
        group_name_exist = cursor.fetchone()
        # if exist: show the error message and return to the profile page
        if group_name_exist:
            flash('Group Already Exist')
            return redirect(url_for('profile'))
        # otherwise insert data into table group: group_name, user_id, group_describe
        cursor.execute('INSERT INTO tb_group (group_name, user_id, group_describe) VALUES (%s, %s, %s)',
                       (group_name, session['user_id'], group_describe))
        mysql.connection.commit()
        # get the group id by desc
        cursor.execute('SELECT group_id FROM tb_group order by -group_id')
        group_id = cursor.fetchone()
        # insert data into table group_members: group_id and user_name
        cursor.execute('INSERT INTO tb_group_members (group_id, user_name) VALUES (%s, %s)',
                       (group_id['group_id'], session['username']))
        mysql.connection.commit()
        return redirect(url_for('profile'))


# group page
@app.route("/into_group/<group_id>")
def into_group(group_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # get the group's information: group_name, group_describe, group_id, group_created_time, group_creater if exist
    cursor.execute('SELECT tb_group.*, tb_group_members.user_name FROM tb_group_members INNER JOIN tb_group'
                   ' ON tb_group.group_id = tb_group_members.group_id WHERE tb_group.group_id = %s', (group_id,))

    group = cursor.fetchone()
    print('group', group)
    # get the group members' information: user_name, user_id
    cursor.execute('SELECT tb_group_members.*, tb_user.user_id FROM tb_group_members INNER JOIN tb_user '
                   'ON tb_group_members.user_name = tb_user.user_name WHERE'
                   ' tb_group_members.group_id = %s', (group_id,))
    group_members = cursor.fetchall()
    session['group_id'] = group_id
    cursor.execute('SELECT tb_chat.*, tb_user.user_name FROM tb_chat INNER JOIN tb_user ON'
                   ' tb_user.user_id = tb_chat.user_id WHERE tb_chat.group_id = %s', (group_id,))
    chat = cursor.fetchall()
    # get all group polls if there exists any
    cursor.execute('SELECT * from tb_poll where group_id = %s', (group_id,))
    polls = cursor.fetchall()
    poll_id_data = []
    poll_ids = ''
    # grab all group poll ID
    for poll in polls:
        poll_id_data.append(poll['poll_id'])
        poll_ids += str(poll['poll_id']) + ','

    # concatenate poll.optionText together grouped by poll_id
    cursor.execute('select tb_group.group_id, tb_poll.poll_id,'
                   ' tb_poll.poll_title, tb_poll.poll_body, group_concat(optionText)'
                   ' from tb_group join tb_poll on tb_group.group_id = tb_poll.group_id join'
                   ' tb_poll_options on tb_poll.poll_id = tb_poll_options.poll_id'
                   ' where tb_poll.poll_id in (select poll_id from tb_poll where poll_id'
                   ' NOT IN (select poll_id from tb_poll_responses where tb_poll_responses.user_id = %s)'
                   ' and group_id = %s) group by poll_id', (session.get('user_id'), group_id,))
    all_options = cursor.fetchall()
    if all_options:
        # attempt to traverse through group_concat(optionText)
        for i in range(0, len(all_options)):
            # print(all_options[i]['group_concat(optionText)'])
            current_poll_option = all_options[i]['group_concat(optionText)'].split(',')
            all_options[i]['group_concat(optionText)'] = all_options[i]['group_concat(optionText)'].split(',')

    else:
        all_options = []

    # get user's voted polls information/data
    cursor.execute('select tb_poll.poll_title, tb_poll.poll_body, tb_poll.poll_id,'
                   ' tb_poll_options.optionText from tb_poll join tb_poll_options on'
                   ' tb_poll.poll_id = tb_poll_options.poll_id join tb_poll_responses'
                   ' on tb_poll_options.option_id = tb_poll_responses.option_id where'
                   ' tb_poll_responses.user_id = %s and tb_poll.group_id = %s', (session.get('user_id'), group_id,))
    voted_polls = cursor.fetchall()
    # set flag not_in_group
    not_in_group = True
    # if the user is a visitor
    if not session.get('user_id'):
        # set flag = True
        not_in_group = True
    # check the user is a group member in this group or not
    else:
        cursor.execute('SELECT * FROM tb_group_members WHERE tb_group_members.user_name = %s AND '
                       'tb_group_members.group_id = %s', (session.get('username'), group_id))
        is_group_member = cursor.fetchone()
        # if the user is a group member in this group, go group page and show all information
        if is_group_member:
            return render_template('group.html', group=group, group_members=group_members, chat=chat,
                                   voted_polls=voted_polls, polls=all_options)
    # otherwise, only show some public information such as group members list, description....
    return render_template('group.html', group=group, group_members=group_members, chat=chat, voted_polls=voted_polls,
                           polls=all_options, not_in_group=not_in_group)


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
            return redirect(url_for('into_group', group_id=group_id))
        # otherwise, check the username if exist in this group
        cursor.execute('SELECT tb_group_members.* FROM tb_group_members INNER JOIN tb_user ON '
                       'tb_group_members.user_name = tb_user.user_name'
                       ' WHERE tb_user.user_name = %s AND tb_group_members.group_id = %s', (user_name, group_id))
        group_member = cursor.fetchall()
        # if this user already in this group, show the error message
        if group_member:
            flash('This User Already in this Group')
            return redirect(url_for('into_group', group_id=group_id))
        # otherwise, see where to place the user by getting their username
        cursor.execute('SELECT user_id FROM tb_user WHERE user_name = %s', (user_name,))
        account = cursor.fetchone();
        where_to_place = 'invitation'

        # check to see if the adder is in the invitees white or black list
        cursor.execute("SELECT user_name_friend FROM tb_whitelist WHERE user_id = %s", ([account['user_id']],))
        friends = cursor.fetchall()
        cursor.execute("SELECT user_name_blocked FROM tb_user_blacklist WHERE user_id =%s", ([account['user_id']]))
        blocked = cursor.fetchall()
        for friend in friends:
            if friend['user_name_friend'] == session['username']:
                where_to_place = "whitelist"
        for block in blocked:
            if block['user_name_blocked'] == session['username']:
                where_to_place = 'blacklist'

        # added in in invitee whitelist automatically add into the group with a message
        if where_to_place == 'whitelist':
            cursor.execute('INSERT INTO tb_group_members (group_id, user_name) VALUES (%s, %s)', (group_id, user_name))
            cursor.execute('INSERT INTO tb_chat (user_id, group_id, chat_content) VALUES (%s, %s, %s)',
                           ([account['user_id']], group_id, "Has joined the group!"))
            mysql.connection.commit()

        # adder is in the blacklist display automatic rejection message in group
        elif where_to_place == 'blacklist':
            cursor.execute('INSERT INTO tb_chat (user_id, group_id, chat_content) VALUES (%s, %s, %s)',
                           ([account['user_id']], group_id,
                            "Thank you for the consideration, but I will not accept invitation to this group."))
            mysql.connection.commit()

        # adder is in neither, send a invitation to the invitee's profile page
        else:
            cursor.execute("SELECT * FROM tb_invite WHERE user_id =%s AND group_id = %s",
                           (account['user_id'], group_id))
            invited = cursor.fetchone()
            # check to see if invitations already sent
            if invited:
                flash('This users is already invited')
            else:
                cursor.execute("INSERT INTO tb_invite (user_id,group_id)" " VALUES (%s,%s)",
                               (account['user_id'], group_id))
                mysql.connection.commit()
        return redirect(url_for('into_group', group_id=group_id))


@app.route('/into_group/<group_id>")', methods=['POST'])
@login_required
def chat(group_id):
    if request.method == 'POST':
        # Create variables for easy access
        chat_content = request.form['chat_content']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Find the current user information
        cursor.execute('SELECT * FROM tb_profile WHERE tb_profile.user_id = %s', [session['user_id']], )
        user_info = cursor.fetchone()
        # if the user_type is Ordinary
        if user_info['user_type'] == 'Ordinary':
            # Check out the taboo word list
            cursor.execute('SELECT * FROM tb_taboo')
            taboo_list = cursor.fetchall()
            # Create a list to save all taboo words the user typed in the post
            taboo_words = []
            for i in range(len(taboo_list)):
                # find all taboo words in the user post_content, ignore all cases
                taboo = re.findall(taboo_list[i]['word'], chat_content, flags=re.IGNORECASE)
                # if exist
                if taboo:
                    # remove repeat taboo words
                    taboo = list(dict.fromkeys(taboo))
                    # add into the list
                    taboo_words += taboo
                    for j in range(len(taboo)):
                        # replace the taboo words to be ***
                        chat_content = chat_content.replace(taboo[j], '***')
            # make all taboo words to be lower case
            taboo_words = [x.lower() for x in taboo_words]
            # remove the repeat taboo words
            taboo_words = list(dict.fromkeys(taboo_words))
            # if taboo_words exist:
            if taboo_words:
                cursor.execute('UPDATE tb_profile SET user_scores = %s WHERE user_id = %s',
                               ((user_info['user_scores'] - 1), session['user_id']))
                mysql.connection.commit()
                flash('Warning! Your Chat contains taboo words, Your Reputation will be reduced by this Rule:'
                      ' First Time use this word : -1 point, Next Time: -5 points ')

                for i in range(len(taboo_words)):
                    # insert taboo words into table user_taboo
                    cursor.execute('INSERT INTO tb_user_taboo (user_id, word) VALUES (%s, %s)',
                                   (session['user_id'], taboo_words[i]))
                    mysql.connection.commit()

                    # find all information of this user in table user_taboo
                    cursor.execute('SELECT * FROM tb_user_taboo WHERE user_id = %s AND word = %s',
                                   (session['user_id'], taboo_words[i]))
                    user_taboo = cursor.fetchall()
                    print(user_taboo)
                    # if this word occurs > 1, scores - 5
                    if len(user_taboo) > 1:
                        cursor.execute('UPDATE tb_profile SET user_scores = %s WHERE user_id = %s',
                                       ((user_info['user_scores'] - 5), session['user_id']))
                        mysql.connection.commit()

        cursor.execute('INSERT INTO tb_chat (user_id, group_id, chat_content) VALUES (%s, %s, %s)',
                       (session['user_id'], group_id, chat_content))
        mysql.connection.commit()
        return redirect(url_for('into_group', group_id=group_id))


@app.route('/group/<group_id>/create-poll', methods=['GET', 'POST'])
def create_poll(group_id):
    if request.method == 'POST':
        title = request.form['poll-title']
        question = request.form['poll-question']
        option = request.form.getlist('poll-option')
        option = ','.join(option)

        # ['option 1', 'option 2']

        # store options into tb_poll_options
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # insert poll into tb_poll
        cursor.execute("INSERT INTO tb_poll (poll_title, poll_body, created_by, group_id)"
                       " VALUES (%s, %s, %s, %s)", (title, question, session['user_id'], group_id))

        # grab newly created poll_id
        cursor.execute("SELECT LAST_INSERT_ID()")
        new_poll_id = cursor.fetchone()
        new_poll_id = new_poll_id['LAST_INSERT_ID()']

        # insert poll options into tb_poll_options
        cursor.callproc('insert_poll_options', [option, new_poll_id])
        mysql.connection.commit()

        return redirect(url_for('into_group', group_id=group_id))


@app.route('/group/<group_id>/poll-vote', methods=['POST'])
def poll_vote(group_id):
    if request.method == 'POST':
        if 'submit-vote' in request.form:
            selected_vote = request.form['poll-option']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # get poll_id and option_id from poll_option
            cursor.execute('SELECT poll_id, option_id from tb_poll_options WHERE optionText = %s', (selected_vote,))
            poll_option_details = cursor.fetchall()
            cursor.execute("INSERT INTO tb_poll_responses (poll_id, option_id, user_id)"
                           " VALUES (%s, %s, %s)", (poll_option_details[0]['poll_id'],
                                                    poll_option_details[0]['option_id'], session['user_id']))
            mysql.connection.commit()
            return redirect(url_for('into_group', group_id=group_id))


if __name__ == '__main__':
    app.run(debug=True)
