from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, BooleanField, DateField, TimeField, TextAreaField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
<<<<<<< Updated upstream
    email = StringField('Email (MMU Student Email)', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
=======
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
>>>>>>> Stashed changes
    faculty = SelectField('Faculty', choices=[
        ('FCI', 'Faculty of Computing & Informatics'),
        ('FOE', 'Faculty of Engineering'),
        ('FOM', 'Faculty of Management'),
        ('FCM', 'Faculty of Creative Multimedia'),
        ('FOL', 'Faculty of Law')
    ])
<<<<<<< Updated upstream
    year = IntegerField('Year of Study', validators=[DataRequired()])
    sport_preferences = StringField('Favorite Sports (comma separated)')
    profile_photo = FileField('Upload Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Sign Up')
=======
    sport_preferences = StringField('Sport Preferences (e.g. Badminton, Football)')
    # FIX: field is called 'picture' — register.html now matches this
    picture = FileField('Profile Picture (optional)',
                        validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Create Account')
>>>>>>> Stashed changes

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
<<<<<<< Updated upstream
            raise ValidationError('That email is already taken.')
=======
            raise ValidationError(
                'That email is already registered. Please use a different one.')

>>>>>>> Stashed changes

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

<<<<<<< Updated upstream
=======

class UpdateProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    faculty = SelectField('Faculty', choices=[
        ('FCI', 'Faculty of Computing and Informatics'),
        ('FOE', 'Faculty of Engineering'),
        ('FOM', 'Faculty of Management'),
        ('FCM', 'Faculty of Creative Multimedia')
    ])
    sport_preferences = StringField('Sport Preferences (comma separated)')
    # FIX: field name is 'picture' to match app.py's form.picture.data
    picture = FileField('Update Profile Picture',
                        validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Save Changes')

    def validate_email(self, email):
        from flask_login import current_user
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('That email is already taken.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    # FIX: was 'confirm_new_password' but change_password.html called it 'confirm_password'
    # Renamed to confirm_password so the template works correctly
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Update Password')


class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    sport_category = SelectField('Sport Category', choices=[
        ('General', 'General Fitness'),
        ('Football', 'Football'),
        ('Basketball', 'Basketball'),
        ('Badminton', 'Badminton'),
        ('Running', 'Running')
    ])
    difficulty = SelectField('Difficulty', choices=[
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard')
    ])
    proof_required = BooleanField('Proof (Photo) Required?')
    submit = SubmitField('Save Task')


class ChallengeForm(FlaskForm):
    title = StringField('Challenge Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    sport_category = StringField('Sport Category', validators=[DataRequired()])
    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    scoring_criteria = StringField('Scoring Criteria (e.g., Max Reps)',
                                   validators=[DataRequired()])
    submit = SubmitField('Save Challenge')


>>>>>>> Stashed changes
class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired()])
    venue = StringField('Venue', validators=[DataRequired()])
    sport_type = StringField('Sport Type', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    max_capacity = IntegerField('Max Capacity', validators=[DataRequired()])
    submit = SubmitField('Create Event')
<<<<<<< Updated upstream
=======


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Reset Password')
>>>>>>> Stashed changes

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

# --- PREVEER'S TASK POOL FORM ---
class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    sport_category = SelectField('Sport Category', choices=[
        ('General', 'General'), 
        ('Running', 'Running'), 
        ('Gym', 'Gym'), 
        ('Badminton', 'Badminton'),
        ('Swimming', 'Swimming')
    ], validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[
        ('Easy', 'Easy'), 
        ('Medium', 'Medium'), 
        ('Hard', 'Hard')
    ], validators=[DataRequired()])
    proof_required = BooleanField('Proof Required?')
    submit = SubmitField('Save Task')

# --- AAHTITIYA'S WEEKLY CHALLENGE FORMS (WEEK 6) ---
class ChallengeForm(FlaskForm):
    title = StringField('Challenge Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    sport_category = SelectField('Sport Category', 
                                 choices=[('Running', 'Running'), 
                                          ('Strength', 'Strength'), 
                                          ('Flexibility', 'Flexibility'), 
                                          ('Team Sports', 'Team Sports'), 
                                          ('Other', 'Other')], 
                                 validators=[DataRequired()])
    deadline = DateTimeLocalField('Submission Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    scoring_criteria = StringField('Scoring Criteria (e.g., Fastest Time, Most Reps)', validators=[DataRequired()])
    submit = SubmitField('Save Challenge')

class SubmissionForm(FlaskForm):
    result = StringField('Your Result (e.g., 25 mins, 50 reps)', validators=[DataRequired()])
    proof_file = FileField('Upload Proof (Image)', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only please!')])
    submit = SubmitField('Submit Proof')