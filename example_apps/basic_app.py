# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

import datetime
from flask import Flask, request, render_template_string
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'THIS IS AN INSECURE SECRET -- Make sure to replace this for production!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app.sqlite'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False

    # Flask-Mail SMTP account settings
    MAIL_USERNAME = 'email@example.com'
    MAIL_PASSWORD = 'password'

    # Flask-User settings
    USER_APP_NAME = "Flask-User Basic App"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"


def create_app():
    """ Flask application factory """
    
    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-Babel
    babel = Babel(app)

    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(app)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)

        # User authentication information
        email = db.Column(db.String(255), nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User information
        first_name = db.Column(db.String(100), nullable=False, server_default='')
        last_name = db.Column(db.String(100), nullable=False, server_default='')

        # Define the relationship to Role via UserRoles
        roles = db.relationship('Role', secondary='user_roles')

    # Define the Role data-model
    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    # Define the UserRoles association table
    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    # Create all database tables
    db.create_all()

    # Create 'user007' user with 'Secret' and 'Agent' roles
    if not User.query.filter(User.email == 'user007@example.com').first():
        user1 = User(
            email='user007@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.password_manager.hash_password('Password1'),
        )
        user1.roles.append(Role(name='Secret'))
        user1.roles.append(Role(name='Agent'))
        db.session.add(user1)
        db.session.commit()

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        return render_template_string("""
                {% extends "flask_user_layout.html" %}
                {% block content %}
                    <h2>{%trans%}Home page{%endtrans%}</h2>
                    <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                    <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                    <p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                    <p><a href={{ url_for('members_page') }}>{%trans%}Member Page{%endtrans%}</a> (login required)</p>
                    <p><a href={{ url_for('special_page') }}>{%trans%}Special Page{%endtrans%}</a> (login with username 'user007' and password 'password')</p>
                    <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
                {% endblock %}
                """)

    # The Members page is only accessible to authenticated users
    @app.route('/members')
    @login_required  # Use of @login_required decorator
    def members_page():
        return render_template_string("""
                {% extends "flask_user_layout.html" %}
                {% block content %}
                    <h2>{%trans%}Members page{%endtrans%}</h2>
                    <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                    <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                    <p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                    <p><a href={{ url_for('members_page') }}>{%trans%}Member Page{%endtrans%}</a> (login required)</p>
                    <p><a href={{ url_for('special_page') }}>{%trans%}Special Page{%endtrans%}</a> (login with username 'user007' and password 'password')</p>
                    <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
                {% endblock %}
                """)

    # The Special page requires ('Secret' AND ('Sauce' or 'Agent')).
    @app.route('/special')
    @roles_required('Secret', ['Sauce', 'Agent'])  # Use of @roles_required decorator
    def special_page():
        return render_template_string("""
                {% extends "flask_user_layout.html" %}
                {% block content %}
                    <h2>{%trans%}Special Page{%endtrans%}</h2>
                    <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                    <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                    <p><a href={{ url_for('home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                    <p><a href={{ url_for('members_page') }}>{%trans%}Member Page{%endtrans%}</a> (login required)</p>
                    <p><a href={{ url_for('special_page') }}>{%trans%}Special Page{%endtrans%}</a> (login with username 'user007' and password 'password')</p>
                    <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
                {% endblock %}
                """)

    return app


# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
