import random
import re
import string
from functools import wraps
from collections import defaultdict

import MySQLdb.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail
from flask_mysqldb import MySQL

app = Flask(__name__)
mail = Mail(app)

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


@app.route("/admin", methods=['get', 'post'])  # admin adding or deleting accounts
def admin():
    # need to make only admin access throgh loginrequired
    if request.method == 'POST':
        # add the account to the database
        if 'Approve' in request.form:
            user_id = request.form['user_id']
            user_name = request.form['username']
            email = request.form['email']
            interest = request.form['interest']
            credential = request.form['credential']
            user_password = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM tb_user WHERE email = %s', (email,))
            account = cursor.fetchone()
            if not account:
                cursor.execute("INSERT INTO tb_user (user_name, user_password, email, credential, interest)"
                               " VALUES (%s, %s, %s, %s, %s)", (user_name, user_password, email, credential, interest))
            cursor.execute("DELETE FROM %s WHERE user_id = %s" % ('tb_applied', user_id))
            mysql.connection.commit()

        # reject the account
        if 'Reject' in request.form:
            user_id = request.form['user_id']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("DELETE FROM %s WHERE user_id = %s" % ('tb_applied', user_id))
            mysql.connection.commit()

    # load the admin page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tb_applied order by user_id')
    # Fetch all post records and return result
    applied = cursor.fetchall()
    if applied:
        return render_template('admin.html', applied=applied)
    return render_template('admin.html')


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
        if email and password == 'admin':
            return redirect(url_for('admin'))
        # If account exists in accounts table in out database
        elif account:
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

        # get all user group evaluations
        cursor.execute('SELECT evaluation_score from tb_user_evaluations where user_id = %s', (session['user_id'],))
        user_scores = cursor.fetchall()
        print(user_scores)

        user_score = 0
        total_score = 0

        # if evaluations_scores exist, add all of them up and divide by length of user_scores
        if (user_scores):
            for i in range(0, len(user_scores)):
                total_score += user_scores[i]['evaluation_score']

            user_score = int(total_score / len(user_scores))
            print(user_score)

            # update user_score in tb_user
            cursor.execute('UPDATE tb_profile SET user_scores = %s WHERE user_id = %s',
                           (user_score, session['user_id']))

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
                       ' ON tb_group.group_id = tb_group_members.group_id AND tb_group_members.user_id = %s AND tb_group.group_status=%s',
                       ( [session['user_id']], 'active',))
        group_info = cursor.fetchall()



        mysql.connection.commit()

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

        # print(final_usernames)

        # get group description
        cursor.execute('SELECT group_describe from tb_group WHERE group_name = %s', (group_name,))
        desc = cursor.fetchone()
        team_desc = desc['group_describe']

        # print('-----------------GROUP DETAILS--------------')
        # print(group)

        # get all group polls if there exists any
        cursor.execute('SELECT * from tb_poll where group_id = %s', (group_id,))
        polls = cursor.fetchall()
        # print(polls)

        poll_id_data = []
        poll_ids = ''
        # grab all group poll ID
        for poll in polls:
            poll_id_data.append(poll['poll_id'])
            poll_ids += str(poll['poll_id']) + ','


        # print(poll_id_data)
        # print(poll_ids)

        # concatenate poll.optionText together grouped by poll_id
        # print('-------------------------------------')
        cursor.execute('select tb_group.group_id, tb_poll.poll_id, tb_poll.poll_title, tb_poll.poll_body, group_concat(optionText) from tb_group join tb_poll on tb_group.group_id = tb_poll.group_id join tb_poll_options on tb_poll.poll_id = tb_poll_options.poll_id where tb_poll.poll_id in (select poll_id from tb_poll where poll_id NOT IN (select poll_id from tb_poll_responses where tb_poll_responses.user_id = %s) and group_id = %s) group by poll_id', (session['user_id'], group_id,))
        all_options = cursor.fetchall()
        # print(all_options)
        if all_options:
            # attempt to traverse through group_concat(optionText)
            for i in range(0, len(all_options)):
                # print(all_options[i]['group_concat(optionText)'])
                current_poll_option = all_options[i]['group_concat(optionText)'].split(',')
                all_options[i]['group_concat(optionText)'] = all_options[i]['group_concat(optionText)'].split(',')
                # print(all_options[i]['group_concat(optionText)'])
            # print(all_options)
        else:
            all_options = []


        # get user's voted polls information/data
        cursor.execute('select tb_poll.poll_title, tb_poll.poll_body, tb_poll.poll_id, tb_poll_options.optionText, tb_poll.vote_count, tb_poll.highest_vote from tb_poll join tb_poll_options on tb_poll.poll_id = tb_poll_options.poll_id join tb_poll_responses on tb_poll_options.option_id = tb_poll_responses.option_id where tb_poll_responses.user_id = %s and tb_poll.group_id = %s', (session['user_id'], group_id,))
        voted_polls = cursor.fetchall();
        print('--------------------VOTED POLL----------------')
        print(voted_polls);

        if not voted_polls:
            voted_polls = []

        # get user's voted_polls poll_id
        if voted_polls:
            for i, poll in enumerate(voted_polls):

                # get highest count option givn poll_id
                cursor.execute('select option_id, COUNT(option_id)  from tb_poll_responses where poll_id = %s group by option_id order by count(option_id) desc limit 1', (poll['poll_id'],))
                poll_highest_vote_count = cursor.fetchone()

                # get poll_highest_vote_count's optionText
                cursor.execute('select optionText from tb_poll_options where option_id = %s', (poll_highest_vote_count['option_id'],))
                highest_vote_option = cursor.fetchone()

                # traverse through voted_poll data and add poll_highest_vote_count into vote_count, and highest_vote_option into highest_vote
                voted_polls[i]['vote_count'] = poll_highest_vote_count['COUNT(option_id)']
                voted_polls[i]['highest_vote'] = highest_vote_option['optionText']

            # print('------------NEW ALTERED VOTED POLL DATA_----------------')
            # print(voted_polls)
        # cursor.execute('SELECT group_status FROM tb_group where group_id = %s', (group_id,))
        # group_status = cursor.fetchone()
        # group_status = group_status['group_status']
        group_status = 'active'

        # get user's group votes forms (ALL) for now
        cursor.execute('SELECT * from tb_group_votes where group_id = %s and user_subject IS NULL UNION SELECT * FROM tb_group_votes where group_id = %s and user_subject != %s', (group_id, group_id, session['user_id'],))
        all_group_votes = cursor.fetchall()
        print('----------all group votes-----------')
        print(all_group_votes)

        user_subject_username = []
        # for all user_subject in group_votes get user_name
        for group_vote in all_group_votes:
            # print(group_vote['user_subject'])
            if group_vote['user_subject'] is not None:
                cursor.execute('SELECT user_name from tb_user where user_id = %s', (group_vote['user_subject'],))
                subject_username = cursor.fetchone()
                user_subject_username.append(subject_username['user_name'])

            else:
                user_subject_username.append(None)

            print(user_subject_username)


        # add subject username into group_vote data
        for i in range(0, len(all_group_votes)):
            if all_group_votes[i]['user_subject'] is not None:
                all_group_votes[i]['user_subject'] = user_subject_username[i]
            else:
                continue
        print('----all group votes-----')
        print(all_group_votes)


        #get user's responded group votes
        cursor.execute('select tb_group_votes.group_id, tb_group_votes.group_vote_id, tb_group_vote_responses.vote_response, tb_group_votes.vote_subject, tb_group_votes.user_subject, tb_group_votes.highest_vote, tb_group_votes.vote_count from tb_group_votes join tb_group_vote_responses on tb_group_votes.group_vote_id = tb_group_vote_responses.group_vote_id where tb_group_vote_responses.voter_id = %s and tb_group_votes.group_id = %s', (session['user_id'], group_id,))
        voted_group_votes = cursor.fetchall()
        print('-----------VOTED GROUP VOTES-----------')

        # replace user_subject id with user_subject usernames
        subject_usernames = []
        # for all user_subject in group_votes get user_name
        for group_vote in voted_group_votes:
            if group_vote['user_subject'] is not None:
                cursor.execute('SELECT user_name from tb_user where user_id = %s', (group_vote['user_subject'],))
                subject_username = cursor.fetchone()
                subject_usernames.append(subject_username['user_name'])
            else:
                subject_usernames.append(None)

        # add subject username into group_vote data
        for i in range(0, len(voted_group_votes)):
            if voted_group_votes[i]['user_subject'] is not None:
                voted_group_votes[i]['user_subject'] = subject_usernames[i]
            else:
                continue


        print(len(voted_group_votes))

        # get highest vote count for each voted group_votes
        if voted_group_votes:
            for i, group_vote in enumerate(voted_group_votes):
                cursor.execute('select group_id, group_vote_id, COUNT(vote_response), vote_response from tb_group_vote_responses where group_vote_id = %s group by vote_response order by COUNT(vote_response) desc limit 1', (group_vote['group_vote_id'],))
                highest_group_vote = cursor.fetchone()

                # store highest group vote count and highest vote response text into voted_group_votes
                voted_group_votes[i]['vote_count'] = highest_group_vote['COUNT(vote_response)']
                voted_group_votes[i]['highest_vote'] = highest_group_vote['vote_response']
        print('-------ALTERED VOTE GROUP VOTE WTIH HIGHEST VOTE AND VOTE COUNT---------')
        print(voted_group_votes)

        # check if all users have voted on USER_RELATED GROUP POLLS
        # get total number of group members in group
        cursor.execute('SELECT COUNT(group_id) from tb_group_members where group_id=%s', (group_id,))
        total_group_members = cursor.fetchone()
        total_group_members = total_group_members['COUNT(group_id)']
        vote_count_needed = total_group_members - 1

        # traverse through all voted_group_polls to see if there is a unanimous vote
        for i, group_vote in enumerate(voted_group_votes):
            cursor.execute('SELECT COUNT(group_vote_id) from tb_group_vote_responses where group_id=%s and group_vote_id=%s', (group_id, group_vote['group_vote_id']))
            total_group_vote_responses = cursor.fetchone()

            cursor.execute('SELECT user_id FROM tb_user where user_name = %s', (group_vote['user_subject'],))
            user_id = cursor.fetchone()
            print(user_id)
            # user_id = user_id['user_id']

            # if total_group_vote_responses['COUNT(group_vote_id)'] = vote_count_needed, DO THE VOTE SUBJECT!!!!
            # get highest_vote, user_subject, vote_subject
            # if total_group_vote_responses['COUNT(group_vote_id)'] == vote_count_needed:
            #     if group_vote['highest_vote'] == 'Yes':
            #         print(group_vote['user_subject'], ' will get a ', group_vote['vote_subject'])
            #         if group_vote['vote_subject'] == 'praise':
            #             cursor.execute('UPDATE tb_group_members SET user_praises = user_praises + 1 where user_id = %s', (user_id,))
            #         elif group_vote['vote_subject'] == 'warning':
            #             cursor.execute('UPDATE tb_group_members SET user_warnings = user_warnings + 1 where user_id = %s', (user_id,))
            #         # else, user will get removed from the group
            #         else:
            #             cursor.execute('DELETE FROM tb_group_members WHERE user_id = %s AND group_id = %s', (user_id, group_id,))
            #
            #     else:
            #         print(group_vote['user_subject'], ' will not get a ', group_vote['vote_subject'])


        mysql.connection.commit()


        return render_template('group_page.html', group=group, members=final_usernames, description=team_desc, polls=all_options, voted_polls=voted_polls, group_status=group_status, group_votes = all_group_votes, voted_group_votes=voted_group_votes)
    else:
        return render_template('404.html')

@app.route('/group/<group_name>/create-poll', methods=['GET', 'POST'])
def create_poll(group_name):
    if request.method == 'POST':
        title = request.form['poll-title']
        question = request.form['poll-question']
        option = request.form.getlist('poll-option')
        option = ','.join(option)

        #['option 1', 'option 2']

        # store options into tb_poll_options


        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # get group_id = where the poll will only be shown
        cursor.execute('SELECT group_id from tb_group where group_name = %s', (group_name,))
        group_id = cursor.fetchone()
        group_id = group_id['group_id']

        # insert poll into tb_poll
        cursor.execute("INSERT INTO tb_poll (poll_title, poll_body, created_by, group_id)"
                               " VALUES (%s, %s, %s, %s)", (title, question, session['user_id'], group_id))

        # grab newly created poll_id
        cursor.execute("SELECT LAST_INSERT_ID()")
        new_poll_id = cursor.fetchone()
        new_poll_id = new_poll_id['LAST_INSERT_ID()']

        # insert poll options into tb_poll_options
        cursor.callproc('insert_poll_options', [option, new_poll_id])

        mysql.connection.commit();


        return redirect(url_for('group_page', group_name=group_name))

@app.route('/group/<group_name>/poll-vote', methods=['POST'])
def poll_vote(group_name):
    if request.method == 'POST':
        if 'submit-vote' in request.form:
            selected_vote = request.form['poll-option']
            # print(selected_vote)

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # get poll_id and option_id from poll_option
            cursor.execute('SELECT poll_id, option_id from tb_poll_options WHERE optionText = %s', (selected_vote,))
            poll_option_details = cursor.fetchall()
            # print(poll_option_details)
            # print(poll_option_details[0]['poll_id'])


            cursor.execute("INSERT INTO tb_poll_responses (poll_id, option_id, user_id)"
                           " VALUES (%s, %s, %s)", (poll_option_details[0]['poll_id'], poll_option_details[0]['option_id'], session['user_id']))

            mysql.connection.commit();

            return redirect(url_for('group_page', group_name=group_name))

@app.route('/group/<group_name>/close', methods=['GET','POST'])
def close_group(group_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # get list of user_id in group (given group_name)
    cursor.execute(''
                   'select tb_user.user_id, tb_user.user_name from tb_user '
                   'join tb_group_members on tb_user.user_id = tb_group_members.user_id '
                   'join tb_group on tb_group_members.group_id = tb_group.group_id '
                   'where tb_group.group_name =%s and tb_user.user_id != %s',
        (group_name, session['user_id']))
    group_members = cursor.fetchall()

    if request.method == 'POST':
        # close_group_data = request.json
        open_reason = request.json['openReason']
        close_reason = request.json['closeReason']
        userRatings = request.json['userRatings']

        print(request.json)
        result = {'url': url_for('home')}

        # iterate through user each user in group - paired with userRating's index
        # insert i = 0, user_id : userRatings in tb_user_evaluation table
        print('--------------EVALUATED GROUP MEMBERS-----------')
        print(group_members)

        # get group_id given group_name
        cursor.execute('SELECT group_id from tb_group where group_name = %s', (group_name,))
        group_id = cursor.fetchone()
        group_id = group_id['group_id']

        for i in range(0, len(userRatings)):
            print(group_members[i]['user_name'], userRatings[str(i)])
            cursor.execute('INSERT INTO tb_user_evaluations (group_id, rater_id, evaluation_score, user_id) VALUES (%s, %s, %s, %s)', (group_id, session['user_id'], userRatings[str(i)], group_members[i]['user_id']))


        # set group_status in tb_group given group_name to 'inactive'
        cursor.execute('UPDATE tb_group SET group_status = %s WHERE group_id = %s', ('inactive', group_id,))

        # insert project evaluation into tb_project_evaluations
        cursor.execute('INSERT INTO tb_project_evaluations (project_open_reason, project_close_reason, group_id) VALUES (%s, %s, %s)', (open_reason, close_reason, group_id,))

        mysql.connection.commit();

        return jsonify(result)


    else:
        return render_template('close_group.html', group_name=group_name, group_members=group_members)


@app.route('/group/<group_name>/create-group-vote', methods=['GET', 'POST'])
def create_groupvote(group_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        cursor.execute('SELECT group_id from tb_group where group_name = %s', (group_name,))
        group_id = cursor.fetchone()
        group_id = group_id['group_id']

        groupvote_title = request.form['groupvote-title']
        groupvote_type = request.form['voteType']

        print('-----------GROUP VOTE FORM SUBMISSION-----------')
        print(groupvote_title, groupvote_type)

        if groupvote_type =='close_group':
            # insert group group-vote
            cursor.execute('INSERT INTO tb_group_votes (group_id, vote_subject, user_id) VALUES (%s, %s, %s)',
                           (group_id, groupvote_type, session['user_id']), )

        user_subject = ''
        if groupvote_type == 'praise' or groupvote_type == 'warning' or groupvote_type == 'user_removal':
            user_subject = request.form['user-subject']
            cursor.execute('SELECT user_id from tb_user where user_name = %s', (user_subject, ))
            user_subject_id = cursor.fetchone()
            user_subject_id = user_subject_id['user_id']

            # insert user group-vote
            cursor.execute('INSERT INTO tb_group_votes (group_id, vote_subject, user_subject, user_id) VALUES (%s, %s, %s, %s)', (group_id, groupvote_type, user_subject_id, session['user_id'],))


        mysql.connection.commit();

    return render_template('close_group.html', group_name=group_name)

@app.route('/group/<group_name>/<group_vote_id>/group-vote-response', methods=['GET', 'POST'])
def groupvote_response(group_name, group_vote_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        if 'submit-groupvote' in request.form:
            groupvote_response = request.form['groupvote-option']
            print(groupvote_response)

            cursor.execute('SELECT group_id from tb_group where group_name = %s', (group_name,))
            group_id = cursor.fetchone()
            group_id = group_id['group_id']

            # insert response to tb_group_vote_responses
            cursor.execute('INSERT INTO tb_group_vote_responses (group_vote_id, group_id, voter_id, vote_response) VALUES (%s, %s, %s, %s)', (group_vote_id, group_id, session['user_id'], groupvote_response))

            mysql.connection.commit();

        return render_template('index.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html')



# invite feature
@app.route("/<group_name>/invite/", methods=['POST'])
def invite(group_name):
    if request.method == 'POST':
        user_name = request.form['user_name']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # get user_id from user_name
        cursor.execute('SELECT user_id FROM tb_user WHERE user_name = %s', (user_name,))
        user_id_exist = cursor.fetchone()
        user_id = user_id_exist['user_id']

        # check the user name the user inputted if exist in user database
        cursor.execute('SELECT user_name FROM tb_user WHERE user_name = %s', (user_name,))
        user_name_exist = cursor.fetchone()

        # get group_id
        cursor.execute('SELECT group_id FROM tb_group WHERE group_name = %s', (group_name,))
        group_id = cursor.fetchone()
        group_id = group_id['group_id']


        # if not exist, output error message, then return to the group page
        if not user_id_exist:
            flash("User doesn't exist")
            return redirect(url_for('group_page', group_name=group_name))
        # otherwise, check the username if exist in this group
        cursor.execute('SELECT tb_group_members.* FROM tb_group_members INNER JOIN tb_user ON '
                       'tb_group_members.user_id = tb_user.user_id'
                       ' WHERE tb_user.user_id = %s AND tb_group_members.group_id = %s', (user_id, group_id))
        group_member = cursor.fetchall()
        # if this user already in this group, show the error message
        if group_member:
            flash('This User Already in this Group')
            return redirect(url_for('group_page', group_name=group_name))

        # otherwise, insert data into table group_members
        cursor.execute('INSERT INTO tb_group_members (group_id, user_id) VALUES (%s, %s)', (group_id, user_id))
        mysql.connection.commit()
        return redirect(url_for('group_page', group_name=group_name))


if __name__ == '__main__':
    app.run(debug=True)