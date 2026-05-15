from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()

# Association table for many-to-many User <-> Badge relationship
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)


class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Point('{self.amount}', '{self.source}', '{self.awarded_at}')"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    faculty = db.Column(db.String(100))
    year = db.Column(db.Integer)
    sport_preferences = db.Column(db.String(200))
    profile_photo = db.Column(db.String(200), default='default.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    points = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    badges = db.relationship('Badge', secondary=user_badges,
                             backref=db.backref('users', lazy='dynamic'))
    tasks = db.relationship('UserTask', backref='user_ref',
                            cascade="all, delete-orphan", lazy=True)
    points_history = db.relationship('Point', backref='user_ref',
                                     cascade="all, delete-orphan", lazy=True)
    rsvps = db.relationship('RSVP', backref='user_ref',
                            cascade="all, delete-orphan", lazy=True)
    # Single relationship for submissions — no duplicate/conflict
    submissions = db.relationship('Submission', backref='submitter',
                                  cascade="all, delete-orphan",
                                  foreign_keys='Submission.user_id',
                                  lazy=True)


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(250))
    category = db.Column(db.String(50), default='General')
    image_file = db.Column(db.String(100), nullable=False, default='default_badge.png')

    def __repr__(self):
        return f"Badge('{self.title}')"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    sport_category = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    proof_required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_tasks = db.relationship('UserTask', backref='task_ref',
                                 cascade="all, delete-orphan", lazy=True)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200))
    sport_type = db.Column(db.String(100))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    max_capacity = db.Column(db.Integer)
    rsvps = db.relationship('RSVP', backref='event_ref',
                            cascade="all, delete-orphan", lazy=True)


class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    waitlisted = db.Column(db.Boolean, default=False)
    checked_in = db.Column(db.Boolean, default=False)


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    sport_category = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    scoring_criteria = db.Column(db.String(200), nullable=False)
    is_closed = db.Column(db.Boolean, default=False)
    submissions = db.relationship('Submission', backref='challenge_ref',
                                  cascade="all, delete-orphan", lazy=True)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    result = db.Column(db.String(200), nullable=False)
    proof_file = db.Column(db.String(200), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    # user relationship uses overlaps to silence the SQLAlchemy warning
    # caused by User.submissions also pointing at this table
    user = db.relationship('User', foreign_keys=[user_id],
                           overlaps="submissions,submitter")


class UserTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    status = db.Column(db.String(20), default='In Progress')
    proof_image = db.Column(db.String(100), nullable=True)
    date_accepted = db.Column(db.DateTime, default=db.func.current_timestamp())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))