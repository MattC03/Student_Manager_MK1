import datetime
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, abort
from sqlalchemy import ForeignKey, Column, String, Integer, Boolean, Text, DateTime, desc
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    firstname = Column(String(250), nullable=False)
    lastname = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    dob = Column(DateTime)
    password = Column(String(250), nullable=False)
    room_id = Column(Integer, db.ForeignKey('room.id'))
    power_value = Column(Integer, nullable=False)
    signed_in = db.Column(Boolean)
    change_password_needed = db.Column(Boolean)
    last_sign_in = db.Column(String)
    last_sign_out = db.Column(String)


class Room(db.Model):
    id = Column(Integer, primary_key=True)
    students = db.relationship('User', backref='room', lazy=True)
    block = Column(String(250), nullable=False)
    number = Column(Integer, nullable=False)
    max_students = Column(Integer, nullable=False)
    number_of_students = Column(Integer, nullable=False)


class Event(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    subheading = Column(String(250), nullable=False)
    url = Column(String(250), nullable=False)
    date = Column(DateTime, nullable=False)
    body = Column(String(250), nullable=False)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.power_value < 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.power_value > 0:
            students = db.session.query(User).filter_by(power_value=0)
            current_year = datetime.datetime.now()
            return render_template("index.html", all_students=students, current_year=current_year)
        else:
            events = Event.query.order_by(Event.date).all()
            return render_template("student-index.html", all_events=events)
    else:
        return redirect((url_for('login')))


@app.route('/register', methods=['GET', 'POST'])
# @login_required
# @admin_only
def register():
    # This function is to be used when the creation of a Admin/Warden user is needed.
    form = forms.RegisterForm()
    if form.validate_on_submit():
        # Checks to see if there is a user with that email already.
        if db.session.query(User).filter_by(email=form.email.data).first():
            flash("There is already have an account with this email!")
            return redirect(url_for("login", form=forms.LoginForm()))

        # Creates a new user from the form.
        new_user = User()
        new_user.email = form.email.data
        new_user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        new_user.firstname = form.firstname.data
        new_user.lastname = form.lastname.data
        new_user.power_value = 1
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))

    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        # checks to see if the email is in the database. If not flashes an error.
        user = db.session.query(User).filter_by(email=form.email.data).first()
        if user is not None:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                # Check to see if password needs update.
                if user.change_password_needed:
                    return redirect(url_for("change_password"))
                return redirect(url_for('index'))
            else:
                flash("Incorrect password, please try again.")
                return redirect(url_for("login", form=form))
        else:
            flash("The email is not recognized please try again or create an account.")
            return redirect(url_for("login", form=form))
    return render_template("login.html", form=form)


@app.route('/change-password/', methods=['GET', 'POST'])
def change_password():
    form = forms.ChangePassword()
    if form.validate_on_submit():
        current_user.password = generate_password_hash(form.new_password.data, method='pbkdf2:sha256',
                                                       salt_length=8)
        current_user.change_password_needed = False
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("change-password.html", form=form)


@app.route('/change-password/<student_id>', methods=['GET', 'POST'])
@login_required
@admin_only
def force_password_change(student_id):
    form = forms.ChangePassword()
    user = db.session.query(User).filter_by(id=student_id).first()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.new_password.data, method='pbkdf2:sha256', salt_length=8)
        user.change_password_needed = True
        db.session.commit()
        return redirect(url_for("all_students"))
    return render_template("change-password.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# #### STUDENT/ROOM MANAGEMENT #####

@app.route('/all-rooms')
@login_required
@admin_only
def all_rooms():
    rooms = db.session.query(Room).all()
    rooms_full = []
    rooms_free = []
    for room in rooms:
        if room.number_of_students < room.max_students:
            rooms_free.append(room)
        else:
            rooms_full.append(room)

    return render_template("all-rooms.html", all_rooms=rooms, rooms_full=rooms_full, rooms_free=rooms_free)


@app.route('/new-room', methods=['GET', 'POST'])
@login_required
@admin_only
def new_room():
    form = forms.CreateRoomForm()
    if form.validate_on_submit():
        # checks to see if the room is already added.
        if not db.session.query(Room).filter_by(block=form.block.data, number=form.number.data).first():
            room_to_add = Room()
            room_to_add.block = form.block.data
            room_to_add.number = form.number.data
            room_to_add.max_students = form.max_students.data
            room_to_add.number_of_students = 0
            db.session.add(room_to_add)
            db.session.commit()
            flash(f"Room {room_to_add.block} {room_to_add.number} has been added")
            return redirect(url_for("index"))
        else:
            flash("Room is already in the system.")
            return render_template('new-room.html', form=form)
    return render_template('new-room.html', form=form)


@app.route('/edit-room/<room_id>', methods=['GET', 'POST'])
@login_required
@admin_only
def edit_room(room_id):
    form = forms.EditRoomForm()
    room = db.session.query(Room).filter_by(id=room_id).first()
    if form.validate_on_submit():
        room.block = form.block.data
        room.number = form.number.data
        room.max_students = form.max_students.data
        room.number_of_students = 0
        db.session.commit()
        flash(f"Room {room.block} {room.number} has been updated")
        return redirect(url_for("all_rooms"))

    form.block.data = room.block
    form.number.data = room.number
    form.max_students.data = room.max_students

    return render_template('new-room.html', form=form)


@app.route('/new-event', methods=['GET', 'POST'])
@login_required
@admin_only
def new_event():
    form = forms.CreateEventForm()
    if form.validate_on_submit():
        event_to_add = Event()
        event_to_add.title = form.title.data
        event_to_add.url = form.url.data
        event_to_add.subheading = form.subheading.data
        event_to_add.body = form.body.data
        event_to_add.date = form.date.data
        db.session.add(event_to_add)
        db.session.commit()
        flash(f"Event {event_to_add.title} has been added")
        return redirect(url_for("index"))
    return render_template('new-event.html', form=form)


@app.route('/all-students')
@login_required
@admin_only
def all_students():
    current_year = datetime.datetime.now()
    students = db.session.query(User).filter_by(power_value=0)
    under18 = []
    over18 = []
    for student in students:
        age = current_year.year - student.dob.year - (
                (current_year.month, current_year.day) < (student.dob.month, student.dob.day))
        if age < 18:
            under18.append(student)
        else:
            over18.append(student)
    return render_template("all-students.html", all_students=students, current_year=current_year, under18=under18,
                           over18=over18)


@app.route("/new-student", methods=['GET', 'POST'])
@login_required
@admin_only
def new_student():
    form = forms.CreateStudentForm()
    # make a list of rooms that have places left in them. Then sets this as the selector list.
    all_rooms_available = [(room.id, f"{room.block} {room.number}") for room in db.session.query(Room).all() if
                           room.number_of_students < room.max_students]
    form.room.choices = all_rooms_available

    # On valid submit of the form it will start the creation of a student.
    if form.validate_on_submit():
        if db.session.query(User).filter_by(email=form.email.data).first():
            flash("There is already an account with this email!")
            return redirect(url_for("login", form=forms.LoginForm()))
        student_to_add = User()
        student_to_add.firstname = form.firstname.data
        student_to_add.lastname = form.lastname.data
        student_to_add.email = form.email.data
        student_to_add.dob = form.dob.data
        student_to_add.room_id = db.session.query(Room).filter_by(id=form.room.data).first().id
        student_to_add.password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
        student_to_add.power_value = 0
        student_to_add.signed_in = True
        student_to_add.change_password_needed = True
        db.session.add(student_to_add)
        db.session.commit()
        # This then increased the amount of students that are in that room.
        student_to_add.room.number_of_students += 1
        db.session.commit()
        flash(f"Student {form.firstname.data} has been created!")
        return redirect(url_for("index"))
    return render_template("new-student.html", form=form)


@app.route("/edit-student/<student_id>/", methods=['GET', 'POST'])
@login_required
@admin_only
def edit_student(student_id):
    form = forms.EditStudentForm()
    # make a list of rooms that have places left in them. Then sets this as the selector list.
    all_rooms_available = [(room.id, f"{room.block} {room.number}") for room in db.session.query(Room).all() if
                           room.number_of_students < room.max_students]
    form.room.choices = all_rooms_available
    student_to_edit = db.session.query(User).filter_by(id=student_id).first()
    # Checks if the student is in a room then adds that to the list of rooms.
    students_room = student_to_edit.room
    if students_room:
        form.room.choices.insert(0, (student_to_edit.room.id, f"{student_to_edit.room.block} {student_to_edit.room.number}"))

    # On valid submit of the form it will start the edit of a student.
    if form.validate_on_submit():
        student_to_edit.firstname = form.firstname.data
        student_to_edit.lastname = form.lastname.data
        student_to_edit.email = form.email.data
        student_to_edit.dob = form.dob.data
        student_to_edit.room_id = form.room.data
        flash(f"Student {form.firstname.data} has been updated!")
        db.session.commit()
        return redirect(url_for("all_students"))

    # Else it will load the page with all the information filled in.
    form.firstname.data = student_to_edit.firstname
    form.lastname.data = student_to_edit.lastname
    form.email.data = student_to_edit.email
    form.dob.data = student_to_edit.dob

    return render_template("edit-student.html", form=form)

# ### STUDENT ACTIONS ### #

@app.route("/student-sign-out")
@login_required
def student_sign_out():
    current_user.signed_in = False
    flash("You have been signed out of site.")
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/student-sign-in")
@login_required
def student_sign_in():
    current_user.signed_in = True
    flash("You have been signed in on site.")
    db.session.commit()
    return redirect(url_for("index"))


# ### DELETE CALLS ### #

@app.route("/delete-room/<int:room_id>")
@login_required
@admin_only
def delete_room(room_id):
    room_to_delete = db.session.query(Room).filter_by(id=room_id).first()
    db.session.delete(room_to_delete)
    db.session.commit()
    return redirect(url_for('all_rooms'))


@app.route("/delete-student/<int:user_id>")
@login_required
@admin_only
def delete_student(user_id):
    user_to_delete = db.session.query(User).filter_by(id=user_id).first()
    room = db.session.query(Room).filter_by(id=user_to_delete.room.id).first()
    room.number_of_students -= 1
    db.session.delete(user_to_delete)
    db.session.commit()
    return redirect(url_for('all_students'))


if __name__ == "__main__":
    app.run(debug=True)
