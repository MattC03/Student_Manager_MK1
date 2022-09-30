from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, URL, InputRequired
from flask_ckeditor import CKEditorField


##WTForm
class CreateAssetForm(FlaskForm):
    asset_id = StringField("Asset Number", validators=[InputRequired()])
    serial_num = StringField("Serial Number", validators=[InputRequired()])
    device = SelectField("Device Type", choices=[("Laptop", "Laptop"), ("Phone", "Phone"), ("Monitor", "Monitor")], validators=[InputRequired()])
    product = StringField("Product", validators=[InputRequired()])
    notes = TextAreaField("Notes")
    decommissioned = BooleanField("Decommissioned")
    submit = SubmitField("Add Asset")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    name = StringField("Name", validators=[InputRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")
