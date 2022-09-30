import datetime
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort
from sqlalchemy import ForeignKey, Column, String, Integer, Boolean, Text
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
    lastname = Column(String(250), nullable=False)
    department = Column(String(250), nullable=False)
    assets = db.relationship('Asset', backref='person', lazy=True)


class Asset(db.Model):
    id = Column(Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'),
                          nullable=False)
    asset_id = Column(String(250), nullable=False, unique=True)
    date_added = Column(String(250), nullable=False)
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
        assets = Asset.query.all()
        return render_template("index.html", all_assets=assets)
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
def new_asset():
    form = forms.CreateAssetForm()
    # Create a list of choices for the person to assign item to.
    form.assigned_to.choices = [f"{person.firstname} {person.lastname}" for person in db.session.query(Person).all()]
    # On a valid submit of the form.
    if form.validate_on_submit():
        # Make sure asset id is not already used.
        if not db.session.query(Asset).filter_by(asset_id=form.asset_id.data).first():
            # Make sure that serial number is not already in there.
            if not db.session.query(Asset).filter_by(asset_id=form.serial_num.data).first():
                # Make the asset and submit it to the database.
                new_asset = Asset(
                    person_id=db.session.query(Person).filter_by(firstname=form.assigned_to.data.split(" ")[0],
                                                                 lastname=form.assigned_to.data.split(" ")[1]).first().id,
                    asset_id=form.asset_id.data,
                    date_added=datetime.date.today().strftime("%B %d, %Y"),
                    serial_num=form.serial_num.data,
                    device=form.device.data,
                    product=form.product.data,
                    added_by=current_user.name,
                    notes=form.notes.data,
                    decommissioned=form.decommissioned.data,
                )
                db.session.add(new_asset)
                db.session.commit()
                flash(f"Asset {form.asset_id.data} has been added!")
                return redirect(url_for("index"))
            else:
                flash("This serial has already been used.")
                return render_template("new-asset.html", form=form)
        else:
            flash("This asset # has already been used.")
            return render_template("new-asset.html", form=form)
    return render_template("new-asset.html", form=form)


@app.route("/new-user", methods=['GET', 'POST'])
def new_user():
    form = forms.CreateUserForm()
    if form.validate_on_submit():
        new_person = Person(
            firstname=form.firstname.data,
            lastname=form.lastname.data,
            department=form.department.data,
        )
        db.session.add(new_person)
        db.session.commit()
        flash(f"User {form.firstname.data} has been created!")
        return redirect(url_for("index"))
    return render_template("new-user.html", form=form)


@app.route("/delete/<int:asset_id>")
def delete_asset(asset_id):
    asset_to_delete = db.session.query(Asset).filter_by(id=asset_id).first()
    db.session.delete(asset_to_delete)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
