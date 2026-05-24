from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MANY-TO-MANY RELATIONSHIP TABLE FOR USER BADGES ---
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id', ondelete='CASCADE'), primary_key=True)
)

# --- USER MODEL ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    faculty = db.Column(db.String(50), nullable=False)
    sport_preferences = db.Column(db.String(200), default="")
    profile_photo = db.Column(db.String(20), nullable=False, default='default.jpg')
    points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    # --- ADDED: columns needed for forgot/reset password feature ---
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Relationships
    rsvps = db.relationship('RSVP', backref='user_ref', lazy=True, cascade="all, delete-orphan")
    usertasks = db.relationship('UserTask', backref='user_ref', lazy=True, cascade="all, delete-orphan")
    submissions = db.relationship('Submission', backref='user_ref', lazy=True, cascade="all, delete-orphan")
    badges = db.relationship('Badge', secondary=user_badges, backref=db.backref('users', lazy='dynamic'))
    point_history = db.relationship('Point', backref='user_ref', lazy=True, cascade="all, delete-orphan")
    streak_history = db.relationship('Streak', backref='user_ref', lazy=True, cascade="all, delete-orphan")

# --- TASK MODEL ---
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    sport_category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    proof_required = db.Column(db.Boolean, default=False)

    usertasks = db.relationship('UserTask', backref='task_ref', lazy=True, cascade="all, delete-orphan")

# --- USER TASK JOURNAL MODEL ---
class UserTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='In Progress')
    proof_image = db.Column(db.String(20), nullable=True)
    date_accepted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# --- BADGE MODEL ---
class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)

# --- EVENT MODEL ---
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    sport_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)

    rsvps = db.relationship('RSVP', backref='event_ref', lazy=True, cascade="all, delete-orphan")

# --- RSVP MODEL ---
class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False)
    waitlisted = db.Column(db.Boolean, default=False)
    checked_in = db.Column(db.Boolean, default=False)

# --- CHALLENGE MODEL ---
class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    sport_category = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    scoring_criteria = db.Column(db.String(100), nullable=False)
    is_closed = db.Column(db.Boolean, default=False)

    submissions = db.relationship('Submission', backref='challenge_ref', lazy=True, cascade="all, delete-orphan")

# --- SUBMISSION MODEL ---
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id', ondelete='CASCADE'), nullable=False)
    result = db.Column(db.String(100), nullable=False)
    proof_file = db.Column(db.String(20), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# --- POINT HISTORY MODEL ---
class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    awarded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# --- STREAK TRACKER MODEL ---
class Streak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    highest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)