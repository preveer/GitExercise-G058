from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     TextAreaField, IntegerField, SelectField, SelectMultipleField,
                     DateField, TimeField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User


FACULTY_CHOICES = [
    ('FCI', 'Faculty of Computing and Informatics'),
    ('FOE', 'Faculty of Engineering'),
    ('FOM', 'Faculty of Management'),
    ('FCM', 'Faculty of Creative Multimedia')
]


class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    faculty = SelectField('Faculty', choices=FACULTY_CHOICES)
    sport_preferences = StringField('Sport Preferences (e.g. Badminton, Football)')
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
    faculty = SelectField('Faculty', choices=FACULTY_CHOICES)
    sport_preferences = StringField('Sport Preferences (comma separated)')
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


class FeedbackForm(FlaskForm):
    submission_type = SelectField('Type', choices=[
        ('Feedback', 'General Feedback / Suggestion'),
        ('Report', 'Bug Report / Inappropriate Content')
    ])
    message = TextAreaField('Your Message', validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField('Submit')


class BuddyAvailabilityForm(FlaskForm):
    # Allow mapping specific times to specific days
    time_choices = [('', 'Not Available'), ('Morning', 'Morning (8am - 12pm)'), ('Afternoon', 'Afternoon (12pm - 5pm)'), ('Evening', 'Evening (5pm - 9pm)')]
   
    mon_time = SelectField('Monday', choices=time_choices)
    tue_time = SelectField('Tuesday', choices=time_choices)
    wed_time = SelectField('Wednesday', choices=time_choices)
    thu_time = SelectField('Thursday', choices=time_choices)
    fri_time = SelectField('Friday', choices=time_choices)
    sat_time = SelectField('Saturday', choices=time_choices)
    sun_time = SelectField('Sunday', choices=time_choices)
   
    submit = SubmitField('Save Availability')
