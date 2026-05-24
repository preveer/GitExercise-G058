from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

# Helper table for many-to-many relationship
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id', ondelete='CASCADE'), primary_key=True)
)


class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Point('{self.amount}', '{self.source}', '{self.awarded_at}')"


# --- USER MODEL ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    faculty = db.Column(db.String(100))
    year = db.Column(db.Integer)
    sport_preferences = db.Column(db.String(200))
    profile_photo = db.Column(db.String(200), default='default.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False) # LUTHRA'S NEW BAN FEATURE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # DAILY TASK TRACKING
    points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    
    # Cascade deletions so deleting a user doesn't crash the DB
    badges = db.relationship('Badge', secondary=user_badges, backref=db.backref('users', lazy='dynamic'))
    tasks = db.relationship('UserTask', backref='user_ref', cascade="all, delete-orphan", lazy=True)
    points_history = db.relationship('Point', backref='user_ref', cascade="all, delete-orphan", lazy=True)
    rsvps = db.relationship('RSVP', backref='user_ref', cascade="all, delete-orphan", lazy=True)

# --- TASK MODEL ---
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250))
    image_file = db.Column(db.String(100), nullable=False, default='default_badge.png')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    sport_category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    proof_required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- BADGE MODEL ---
class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)

# --- EVENT MODEL ---
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200))
    sport_type = db.Column(db.String(100))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    max_capacity = db.Column(db.Integer)

    rsvps = db.relationship('RSVP', backref='event_ref', lazy=True, cascade="all, delete-orphan")

# --- RSVP MODEL ---
class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False)
    waitlisted = db.Column(db.Boolean, default=False)
    checked_in = db.Column(db.Boolean, default=False)

# NEW: MISSING CHALLENGE AND SUBMISSION MODELS FIXED
class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref=db.backref('submissions', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class UserTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    status = db.Column(db.String(20), default='In Progress')
    proof_image = db.Column(db.String(100), nullable=True)
    date_accepted = db.Column(db.DateTime, default=db.func.current_timestamp())
    task = db.relationship('Task', backref=db.backref('assigned_users', lazy=True))