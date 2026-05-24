from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DateField, TimeField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

# --- REGISTRATION FORM ---
class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    faculty = SelectField('Faculty', choices=[
        ('', 'Select Faculty'),
        ('FOM', 'Faculty of Management (FOM)'),
        ('FOE', 'Faculty of Engineering (FOE)'),
        ('FCI', 'Faculty of Computing & Informatics (FCI)'),
        ('FAC', 'Faculty of Cinematic Arts (FAC)'),
        ('FIST', 'Faculty of Information Science & Technology (FIST)')
    ], validators=[DataRequired()])
    sport_preferences = StringField('Sport Preferences (e.g., Football, Running)', validators=[Length(max=200)])
    picture = FileField('Upload Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

# --- LOGIN FORM ---
class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# --- UPDATE PROFILE FORM ---
class UpdateProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    faculty = SelectField('Faculty', choices=[
        ('FOM', 'Faculty of Management (FOM)'),
        ('FOE', 'Faculty of Engineering (FOE)'),
        ('FCI', 'Faculty of Computing & Informatics (FCI)'),
        ('FAC', 'Faculty of Cinematic Arts (FAC)'),
        ('FIST', 'Faculty of Information Science & Technology (FIST)')
    ], validators=[DataRequired()])
    sport_preferences = StringField('Sport Preferences', validators=[Length(max=200)])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')

# --- CHANGE PASSWORD FORM ---
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')

# --- FORGOT & RESET PASSWORD FORMS ---
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

# --- ADMIN: EVENT FORM ---
class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    venue = StringField('Venue', validators=[DataRequired(), Length(max=100)])
    sport_type = StringField('Sport Type', validators=[DataRequired(), Length(max=50)])
    date = DateField('Event Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Event Time', format='%H:%M', validators=[DataRequired()])
    max_capacity = IntegerField('Maximum Capacity', validators=[DataRequired()])
    submit = SubmitField('Create Event')

# --- ADMIN: TASK FORM ---
class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    sport_category = StringField('Sport Category', validators=[DataRequired(), Length(max=50)])
    difficulty = SelectField('Difficulty Level', choices=[
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard')
    ], validators=[DataRequired()])
    proof_required = BooleanField('Require Image Proof Submission')
    submit = SubmitField('Save Task')

# --- ADMIN: CHALLENGE FORM ---
class ChallengeForm(FlaskForm):
    title = StringField('Challenge Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    sport_category = StringField('Sport Category', validators=[DataRequired(), Length(max=50)])
    deadline = DateField('Submission Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    scoring_criteria = StringField('Scoring Criteria (e.g., Fastest Time, Most Reps)', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Challenge')

# --- ADMIN: BADGE FORM ---
class BadgeForm(FlaskForm):
    title = StringField('Badge Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Criteria Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Streak', 'Streak Achievements'),
        ('Event', 'Event Participation'),
        ('Challenge', 'Challenge Domination'),
        ('Admin', 'Special Recognition')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Badge')