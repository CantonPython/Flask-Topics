# -*- coding: utf-8 -*-

from datetime import datetime
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, \
    render_template, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash
import time
import os
import hashlib
from .model import Session, User, Topic, UsernameTaken

# configuration
DATABASE = os.path.dirname(__file__) + '/../topics.db'
# used for sessions
SECRET_KEY = 'odAVG3OOUb5fGA'
db_session = Session()
app = Flask('topic_creator')
app.config.from_object(__name__)


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('select user_id from user where username = ?',
                  [username], one=True)
    return rv[0] if rv else None


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.get_by_id(db_session, session['user_id'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('topics'))
    error = None
    if request.method == 'POST':
        user = User.get_by_username(Session(), request.form['username'])

        if user is None:
            error = 'Invalid username'
        elif not user.passwd == hash(request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user.id
            return redirect(url_for('topics'))
    return render_template('login.html', error=error)


def hash(value):
    md5 = hashlib.md5()
    md5.update(value.encode("utf-8"))
    return md5.hexdigest()


@app.route('/')
def all_topics():
    """Shows all topics submitted."""
    topics = db_session.query(Topic)
    return render_template('topics.html', topics=topics)


@app.route('/add_topic', methods=['GET', 'POST'])
def add_topic():
    if not g.user:
        return redirect('/')

    if request.method == 'POST':
        description = request.form['description']
        if not description:
            return render_template('add_topic.html', error="Description is required")
        else:
            topic = Topic(request.form["description"])
            topic.author = g.user
            db_session.add(topic)
            db_session.commit()

            return redirect(url_for('topics'))
    else:
        return render_template('add_topic.html')


@app.route('/topics')
def topics():
    if not g.user:
        return redirect('/')

    topics = Topic.get_all_by_author(db_session, session['user_id'])
    return render_template('topics.html', topics=topics)


@app.route('/upvote/<topic_id>')
def upvote(topic_id):
    if not g.user:
        return redirect('/')

    topic = Topic.get_by_id(db_session, topic_id)
    topic.upvote(db_session, g.user)

    return redirect(url_for('all_topics'))


@app.route('/downvote/<topic_id>')
def downvote(topic_id):
    if not g.user:
        return redirect('/')

    topic = Topic.get_by_id(db_session, topic_id)
    topic.downvote(db_session, g.user)

    return redirect(url_for('all_topics'))


def user_already_voted(topic_id):
    votes = query_db('''
         select * from user_topic where user_id = ? and topic_id = ?
    ''', [session['user_id'], topic_id])

    return True if votes else False


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('topics'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
            error = 'The username is already taken'
        else:
            try:
                new_user = User(request.form["username"], request.form["email"], request.form["password"])
                db_session.add(new_user)
                db_session.commit()
                flash('You were successfully registered and can login now')
                return redirect(url_for('login'))
            except Exception as e:
                db_session.rollback()
                error = e 

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('all_topics'))


# some functions for templates
def is_current_path(path):
    return request.path == path


app.jinja_env.globals.update(is_current_path=is_current_path)
