from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()

user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    badges = db.relationship('Badge', secondary=user_badges, backref=db.backref('users', lazy='dynamic'))


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250))
    image_file = db.Column(db.String(100), nullable=False, default='default_badge.png')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))