from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     TextAreaField, IntegerField, SelectField,
                     DateField, TimeField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User


class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    faculty = SelectField('Faculty', choices=[
        ('FCI', 'Faculty of Computing and Informatics'),
        ('FOE', 'Faculty of Engineering'),
        ('FOM', 'Faculty of Management'),
        ('FCM', 'Faculty of Creative Multimedia')
    ])
    sport_preferences = StringField('Sport Preferences (e.g. Badminton, Football)')
    # FIX: field is called 'picture' — register.html now matches this
    picture = FileField('Profile Picture (optional)',
                        validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Create Account')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'That email is already registered. Please use a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


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


class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired()])
    venue = StringField('Venue', validators=[DataRequired()])
    sport_type = StringField('Sport Type', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    max_capacity = IntegerField('Max Capacity', validators=[DataRequired()])
    submit = SubmitField('Create Event')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Reset Password')


class BadgeForm(FlaskForm):
    title = StringField('Badge Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Milestone', 'Points Milestone'),
        ('Streak', 'Streak Achievement'),
        ('Event', 'Event Participation'),
        ('Competition', 'Challenge Winner')
    ])
    submit = SubmitField('Save Badge')


class FeedbackForm(FlaskForm):
    submission_type = SelectField('Type', choices=[
        ('Feedback', 'General Feedback / Suggestion'),
        ('Report', 'Bug Report / Inappropriate Content')
    ])
    message = TextAreaField('Your Message', validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField('Submit')


class BuddyAvailabilityForm(FlaskForm):
    availability_days = SelectMultipleField('Days You Are Free', choices=[
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    ])
    availability_time = SelectField('Preferred Time', choices=[
        ('Morning', 'Morning (8am - 12pm)'),
        ('Afternoon', 'Afternoon (12pm - 5pm)'),
        ('Evening', 'Evening (5pm - 9pm)'),
    ])
    submit = SubmitField('Save Availability')