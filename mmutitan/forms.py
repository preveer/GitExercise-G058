from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    # Field 1: Name
    name = StringField('Full Name', 
                       validators=[DataRequired(), Length(min=2, max=100)])
    
    # Field 2: Email (with validation)
    email = StringField('Email (MMU Student Email)', 
                        validators=[DataRequired(), Email()])
    
    # Field 3: Password
    password = PasswordField('Password', 
                             validators=[DataRequired(), Length(min=6)])
    
    # Field 4: Confirm Password
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    
    # Field 5: Faculty (Dropdown)
    faculty = SelectField('Faculty', choices=[
        ('FCI', 'Faculty of Computing & Informatics'),
        ('FOE', 'Faculty of Engineering'),
        ('FOM', 'Faculty of Management'),
        ('FCM', 'Faculty of Creative Multimedia'),
        ('FOL', 'Faculty of Law')
    ])
    
    # Field 6: Year of Study
    year = IntegerField('Year of Study', validators=[DataRequired()])
    
    # Field 7: Sport Preferences
    sport_preferences = StringField('Favorite Sports (comma separated)')
    
    # Field 8: Profile Photo
    profile_photo = FileField('Upload Profile Photo', 
                              validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    
    submit = SubmitField('Sign Up')

    # This custom check prevents duplicate emails in your database
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

# --- CARD 2: LOGIN FORM ---
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')