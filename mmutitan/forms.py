from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, BooleanField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email (MMU Student Email)', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    faculty = SelectField('Faculty', choices=[
        ('FCI', 'Faculty of Computing & Informatics'),
        ('FOE', 'Faculty of Engineering'),
        ('FOM', 'Faculty of Management'),
        ('FCM', 'Faculty of Creative Multimedia'),
        ('FOL', 'Faculty of Law')
    ])
    year = IntegerField('Year of Study', validators=[DataRequired()])
    sport_preferences = StringField('Favorite Sports (comma separated)')
    profile_photo = FileField('Upload Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired()])
    venue = StringField('Venue', validators=[DataRequired()])
    sport_type = StringField('Sport Type', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    max_capacity = IntegerField('Max Capacity', validators=[DataRequired()])
    submit = SubmitField('Create Event')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                    validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')

class UpdateProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    faculty = SelectField('Faculty', choices=[
        ('FCI', 'Faculty of Computing & Informatics'),
        ('FOE', 'Faculty of Engineering'),
        ('FOM', 'Faculty of Management'),
        ('FCM', 'Faculty of Creative Multimedia'),
        ('FOL', 'Faculty of Law')
    ])
    year = IntegerField('Year of Study', validators=[DataRequired()])
    sport_preferences = StringField('Favorite Sports')
    profile_photo = FileField('Update Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')