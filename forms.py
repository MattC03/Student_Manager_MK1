from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, URL, InputRequired
from flask_ckeditor import CKEditorField
from main import db
from main import Person

##WTForm
class CreateAssetForm(FlaskForm):
    asset_id = StringField("Asset Number", validators=[InputRequired()])
    serial_num = StringField("Serial Number", validators=[InputRequired()])
    assigned_to = SelectField("Assigned To", validators=[InputRequired()])
    device = SelectField("Device Type", choices=[("Laptop", "Laptop"), ("Phone", "Phone"), ("Monitor", "Monitor")], validators=[InputRequired()])
    product = StringField("Product", validators=[InputRequired()])
    notes = TextAreaField("Notes")
    decommissioned = BooleanField("Decommissioned")
    submit = SubmitField("Add Asset")


class CreateUserForm(FlaskForm):
    firstname = StringField("First Name", validators=[InputRequired()])
    lastname = StringField("Last Name", validators=[InputRequired()])
    department = StringField("Department", validators=[InputRequired()])
    submit = SubmitField("Add User")

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    name = StringField("Name", validators=[InputRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")
