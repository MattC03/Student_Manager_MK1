from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, TextAreaField, BooleanField, HiddenField, \
    DateField, EmailField, IntegerField
from wtforms.validators import DataRequired, URL, InputRequired, EqualTo, Email


##WTForm

class CreateStudentForm(FlaskForm):
    firstname = StringField("First Name", validators=[InputRequired()])
    lastname = StringField("Last Name", validators=[InputRequired()])
    email = EmailField("Students Email", validators=[InputRequired(), Email()])
    dob = DateField("Date of Birth", validators=[InputRequired()])
    room = SelectField("Room", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Add Student")


class CreateRoomForm(FlaskForm):
    block = StringField("Block", validators=[InputRequired()])
    number = IntegerField("Room Number", validators=[InputRequired()])
    max_students = IntegerField("Maximum Students", validators=[InputRequired()])


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    name = StringField("Name", validators=[InputRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")
