from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, EqualTo
from flask_wtf.file import FileField

# Login Form
class LoginForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")
	
# Create a Form Class
class UserForm(FlaskForm):
	name = StringField("Name", validators=[DataRequired()])
	username = StringField("UserName", validators=[DataRequired()])
	email = StringField("Email", validators=[DataRequired()])
	field = StringField("Field")
	about_author = TextAreaField("About Author")
	password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message='Passwords Must Match!')])
	password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
	profile_pic = FileField('Profile Pic')
	submit = SubmitField("Submit")
	
class RegistrationForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class GroupForm(FlaskForm):
	name = StringField('Group Name', validators=[DataRequired()])
	description = TextAreaField('Group Description', validators=[DataRequired()])
	submit = SubmitField('Submit')

class JoinForm(FlaskForm):
	code = StringField('Group Code', validators=[DataRequired()])
	submit = SubmitField('Join')