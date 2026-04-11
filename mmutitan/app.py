from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        from models import (User, Task, DailyAssignment,
                           Streak, Point, Event, RSVP,
                           Challenge, Submission,
                           BuddyRequest, Feedback)
        db.create_all()

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

    @app.route('/')
    def home():
        return render_template('base.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)