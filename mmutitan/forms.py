from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, BooleanField, DateField, TimeField, TextAreaField, DateTimeLocalField
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
    year = IntegerField('Year of Study', validators=[DataRequired()])
    sport_preferences = StringField('Favorite Sports (comma separated)')
    profile_photo = FileField('Upload Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Sign Up')

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
        ('FCM', 'Faculty of Creative Multimedia'),
        ('FOL', 'Faculty of Law')
    ])
    year = IntegerField('Year of Study', validators=[DataRequired()])
    sport_preferences = StringField('Favorite Sports')
    profile_photo = FileField('Update Profile Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')


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

class SubmissionForm(FlaskForm):
    result = StringField('Your Result (e.g., 25 mins, 50 reps)', validators=[DataRequired()])
    proof_file = FileField('Upload Proof (Image)', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only please!')])
    submit = SubmitField('Submit Proof')