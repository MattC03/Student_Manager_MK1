from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort
from sqlalchemy import ForeignKey, Column, String, Integer, Boolean, Text, DateTime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import forms

# import ldap3

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
    power_value = Column(Integer, nullable=False)


class Room(db.Model):
    id = Column(Integer, primary_key=True)
    students = db.relationship('Student', backref='room', lazy=True)
    block = Column(String(250), nullable=False)
    number = Column(Integer, nullable=False)
    max_students = Column(Integer, nullable=False)
    number_of_students = Column(Integer, nullable=False)


class Student(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    firstname = Column(String(250), nullable=False)
    lastname = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    dob = Column(DateTime, nullable=False)
    password = Column(String(250), nullable=False)
    room_id = Column(Integer, nullable=False)
    power_value = Column(Integer, nullable=False)
    signed_in = db.Column(Boolean, nullable=False)
    last_sign_in = db.Column(String)
    last_sign_out = db.Column(String)


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.power_value != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    if current_user.is_authenticated:
        students = Student.query.all()
        return render_template("index.html", all_students=students)
    else:
        return redirect((url_for('login')))


@app.route('/register', methods=['GET', 'POST'])
# @login_required
# @admin_only
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
        new_user.power_value = 0
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


@app.route('/new-room')
def new_room():
    form=forms.CreateRoomForm
    return render_template('new-room.html', form=form)


@app.route("/new-student", methods=['GET', 'POST'])
@login_required
def new_student():
    form = forms.CreateStudentForm()
    # make a list of rooms that have places left in them. Then sets this as the selector list.
    all_rooms_available = [(room.id, f"{room.number, room.block}") for room in db.session.query(Room).all() if
                           room.number_of_students < room.max_students]
    form.room.choices = all_rooms_available

    # On valid submit of the form it will start the creation of a student.
    if form.validate_on_submit():
        student_to_add = Student()
        student_to_add.firstname = form.firstname.data
        student_to_add.lastname = form.lastname.data
        student_to_add.email = form.email.data
        student_to_add.dob = form.dob.data
        student_to_add.room_id = db.session.query(Room).filter_by(number="1", block="test")
        student_to_add.password = form.password.data
        student_to_add.power_value = 0
        db.session.add(student_to_add)
        db.session.commit()
        flash(f"Student {form.firstname.data} has been created!")
        return redirect(url_for("index"))
    return render_template("new-student.html", form=form)


# #### ASSET MANAGEMENT #####

@app.route("/delete-room/<int:room_id>")
@admin_only
def delete_asset(room_id):
    room_to_delete = db.session.query(Room).filter_by(id=room_id).first()
    db.session.delete(room_to_delete)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
