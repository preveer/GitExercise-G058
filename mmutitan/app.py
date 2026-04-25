from flask import Flask, render_template, url_for, flash, redirect
from flask_login import login_user, current_user, logout_user, login_required
from models import db, login_manager, User, Badge, Event, RSVP
from forms import RegistrationForm, LoginForm, EventForm
from config import Config
from forms import ChangePasswordForm

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        # If logged in, maybe show a dashboard. If not, show welcome.
        return render_template('home.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data,
                faculty=form.faculty.data,
                year=form.year.data,
                sport_preferences=form.sport_preferences.data
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.password == form.password.data:
                login_user(user, remember=form.remember.data)
                flash('Welcome back to the Titan Arena!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Login Unsuccessful. Check email and password.', 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        # Redirecting to login so the user sees a change
        return redirect(url_for('login'))

    @app.route('/admin/events', methods=['GET', 'POST'])
    @login_required
    def manage_events():
        form = EventForm()
        if form.validate_on_submit():
            new_event = Event(
                name=form.name.data, venue=form.venue.data,
                sport_type=form.sport_type.data, date=form.date.data,
                time=form.time.data, max_capacity=form.max_capacity.data
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Event successfully created!', 'success')
            return redirect(url_for('manage_events'))
        events = Event.query.all()
        return render_template('admin_events.html', events=events, form=form)

    @app.route('/events')
    @login_required
    def list_events():
        events = Event.query.all()
        return render_template('events.html', events=events)

    @app.route('/rsvp/<int:event_id>', methods=['POST'])
    @login_required
    def rsvp(event_id):
        event = Event.query.get_or_404(event_id)
        existing_rsvp = RSVP.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        if existing_rsvp:
            flash('Already RSVP\'d!', 'info')
            return redirect(url_for('list_events'))

        count = RSVP.query.filter_by(event_id=event.id, waitlisted=False).count()
        new_rsvp = RSVP(user_id=current_user.id, event_id=event.id, waitlisted=(count >= event.max_capacity))
        db.session.add(new_rsvp)
        db.session.commit()
        flash('RSVP Successful!', 'success')
        return redirect(url_for('list_events'))
    
    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        form = ChangePasswordForm()
        if form.validate_on_submit():
            # Verify if the current password matches what is in our database
            if current_user.password == form.old_password.data:
                current_user.password = form.new_password.data
                db.session.commit()
                flash('Your password has been updated successfully!', 'success')
                return redirect(url_for('home'))
            else:
                # If they got their own password wrong, show an error
                flash('Update Failed. Current password is incorrect.', 'danger')
        return render_template('change_password.html', title='Change Password', form=form)
    
    @app.route('/profile')
    @login_required
    def profile():
        # We use current_user to get the logged-in person's data
        return render_template('profile.html', title='My Profile', user=current_user)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)