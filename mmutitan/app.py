from flask import Flask, render_template, url_for, flash, redirect
from flask_login import login_user, current_user, logout_user, login_required
from models import db, login_manager, User, Badge, Event, RSVP
from forms import RegistrationForm, LoginForm, EventForm
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        return render_template('base.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                name=form.name.data,
                email=form.email.data,
                password=form.password.data, # Note: Hashing is usually done here for real apps
                faculty=form.faculty.data,
                year=form.year.data,
                sport_preferences=form.sport_preferences.data
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created! You can now log in.', 'success')
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
        return redirect(url_for('home'))

    # --- AAHTITIYA'S FIXED ROUTE  ---
    @app.route('/admin/events', methods=['GET', 'POST'])
    def manage_events():
        form = EventForm()
        if form.validate_on_submit():
            new_event = Event(
                name=form.name.data,
                venue=form.venue.data,
                sport_type=form.sport_type.data,
                date=form.date.data,
                time=form.time.data,
                max_capacity=form.max_capacity.data
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Event successfully created!', 'success')
            return redirect(url_for('manage_events'))
        
        events = Event.query.all()
        return render_template('admin_events.html', events=events, form=form)

    # --- TASK 2: VIEW EVENTS & RSVP ---
    @app.route('/events')
    @login_required
    def list_events():
        events = Event.query.all()
        return render_template('events.html', events=events)

    @app.route('/rsvp/<int:event_id>', methods=['POST'])
    @login_required
    def rsvp(event_id):
        event = Event.query.get_or_404(event_id)
        
        # 1. Check if the user already joined
        existing_rsvp = RSVP.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        if existing_rsvp:
            flash('You are already on the list for this event!', 'info')
            return redirect(url_for('list_events'))

        # 2. Check how many people are currently going (excluding waitlist)
        current_rsvps = RSVP.query.filter_by(event_id=event.id, waitlisted=False).count()
        
        # 3. The Waitlist Math
        is_waitlisted = current_rsvps >= event.max_capacity

        # 4. Save to database
        new_rsvp = RSVP(user_id=current_user.id, event_id=event.id, waitlisted=is_waitlisted)
        db.session.add(new_rsvp)
        db.session.commit()

        if is_waitlisted:
            flash(f'Event is full! You have been added to the WAITLIST for {event.name}.', 'warning')
        else:
            flash(f'Successfully RSVP\'d for {event.name}!', 'success')
            
        return redirect(url_for('list_events'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)