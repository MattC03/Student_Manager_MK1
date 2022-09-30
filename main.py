from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort
from datetime import date
from sqlalchemy import ForeignKey, Column, String, Integer, Boolean, DateTime, Text
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import forms
import ldap3

##SETUP APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

##LDAP Connection


##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asset_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    name = Column(String(255), unique=True, nullable=True)
    password = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)


class Person(db.Model):
    id = Column(Integer, primary_key=True)
    firstname = Column(String(250), nullable=False)
    surname = Column(String(250), nullable=False)
    department = Column(String(250), nullable=False)
    assets = db.relationship('Asset', backref='person', lazy=True)


class Asset(db.Model):
    id = Column(Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                          nullable=False)
    asset_id = Column(Integer, nullable=False, unique=True)
    date_added = Column(DateTime, nullable=False)
    serial_num = Column(String(250), nullable=False, unique=True)
    device = Column(String(250), nullable=False)
    product = Column(String(250), nullable=False)
    added_by = Column(String(250), nullable=False)
    notes = Column(Text, nullable=False)
    decommissioned = Column(Boolean)


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "Admin":
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    if current_user.is_authenticated:
        posts = Asset.query.all()
        return render_template("index.html", all_posts=posts)
    else:
        return redirect((url_for('login')))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        # Checks to see if there is a user with that email already.
        if db.session.query(User).filter_by(email=form.email.data).first():
            flash("You already have an account please sign in below.")
            return redirect(url_for("login", form=forms.LoginForm()))

        # Creates a new user from the form.
        new_user = User()
        new_user.email = form.email.data
        new_user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        new_user.name = form.name.data
        new_user.role = "User"
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user is not None:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Incorrect password, please try again.")
                return redirect(url_for("login", form=form))
        else:
            flash("The email is not recognized please try again or create an account.")
            return redirect(url_for("login", form=form))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/new-asset", methods=['GET', 'POST'])
@admin_only
def new_asset():
    form = forms.CreateAssetForm()
    if form.validate_on_submit():
        new_post = Asset(
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("new-asset.html", form=form)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = Asset.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
