import os
import secrets
import random
from datetime import date, datetime
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from models import db, login_manager, User, Badge, Event, RSVP, Task, UserTask, Point, Streak
from forms import (RegistrationForm, LoginForm, EventForm, 
                   ChangePasswordForm, UpdateProfileForm, TaskForm)
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        db.create_all()

    # --- HELPER FUNCTIONS ---
    
    def save_picture(form_picture):
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
        form_picture.save(picture_path)
        return picture_fn

    def award_points(user_id, amount, source):
        """Logs point transactions in the database."""
        new_point = Point(user_id=user_id, amount=amount, source=source)
        db.session.add(new_point)
        # We don't commit here so the calling route can handle the final commit

    # --- ROUTES ---

    @app.route('/')
    def home():
        if current_user.is_authenticated:
            return render_template('dashboard.html', title='Dashboard')
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
        return redirect(url_for('login'))

    # --- LUTHRA'S PROFILE ROUTES ---

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', title='My Profile', user=current_user)

    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        form = UpdateProfileForm()
        if form.validate_on_submit():
            if form.profile_photo.data:
                picture_file = save_picture(form.profile_photo.data)
                current_user.profile_photo = picture_file
            current_user.name = form.name.data
            current_user.faculty = form.faculty.data
            current_user.year = form.year.data
            current_user.sport_preferences = form.sport_preferences.data
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.name.data = current_user.name
            form.faculty.data = current_user.faculty
            form.year.data = current_user.year
            form.sport_preferences.data = current_user.sport_preferences
        return render_template('edit_profile.html', title='Edit Profile', form=form)

    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if current_user.password == form.old_password.data:
                current_user.password = form.new_password.data
                db.session.commit()
                flash('Your password has been updated!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Update Failed. Current password is incorrect.', 'danger')
        return render_template('change_password.html', title='Change Password', form=form)

    # --- AAHTITIYA'S EVENT ROUTES ---

    @app.route('/admin/events', methods=['GET', 'POST'])
    @login_required
    def manage_events():
        if not current_user.is_admin:
            flash('Access denied.', 'danger')
            return redirect(url_for('home'))
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
        user_rsvps = {rsvp.event_id: rsvp for rsvp in RSVP.query.filter_by(user_id=current_user.id).all()}
        spots_left = {}
        for event in events:
            confirmed_count = RSVP.query.filter_by(event_id=event.id, waitlisted=False).count()
            spots_left[event.id] = event.max_capacity - confirmed_count
        return render_template('events.html', events=events, user_rsvps=user_rsvps, spots_left=spots_left)

    @app.route('/rsvp/<int:event_id>', methods=['POST'])
    @login_required
    def rsvp(event_id):
        event = Event.query.get_or_404(event_id)
        existing_rsvp = RSVP.query.filter_by(user_id=current_user.id, event_id=event.id).first()
        if existing_rsvp:
            flash('Already RSVP\'d!', 'info')
            return redirect(url_for('list_events'))
        count = RSVP.query.filter_by(event_id=event.id, waitlisted=False).count()
        new_rsvp = RSVP(user_id=current_user.id, event_id=event.id, 
                        waitlisted=(count >= event.max_capacity))
        db.session.add(new_rsvp)
        db.session.commit()
        flash('RSVP Successful!', 'success')
        return redirect(url_for('list_events'))

    @app.route('/checkin/<int:event_id>', methods=['POST'])
    @login_required
    def checkin(event_id):
        rsvp = RSVP.query.filter_by(user_id=current_user.id, event_id=event_id).first()
        if rsvp and not rsvp.waitlisted and not rsvp.checked_in:
            rsvp.checked_in = True
            
            # AWARD POINTS VIA LOG SYSTEM
            award_points(current_user.id, 50, f"Event Attendance: {event_id}")
            current_user.points += 50 
            
            # Award Badge
            event_badge = Badge.query.filter_by(title="Event Attended").first()
            if not event_badge:
                event_badge = Badge(title="Event Attended", description="Attended a campus sporting event!")
                db.session.add(event_badge)
            
            if event_badge not in current_user.badges:
                current_user.badges.append(event_badge)
            
            db.session.commit()
            flash('Checked in! +50 Points and Badge earned!', 'success')
        else:
            flash('Check-in failed. You must have a confirmed spot.', 'danger')
        return redirect(url_for('list_events'))

    # --- PREVEER'S TASK & POINTS ROUTES ---

    @app.route('/daily_tasks')
    @login_required
    def daily_tasks():
        today = date.today()
        today_tasks = UserTask.query.filter(
            UserTask.user_id == current_user.id,
            db.func.date(UserTask.date_accepted) == today
        ).all()

        if len(today_tasks) == 0:
            pool = Task.query.all()
            if len(pool) > 0:
                chosen_tasks = random.sample(pool, min(3, len(pool)))
                for t in chosen_tasks:
                    new_ut = UserTask(user_id=current_user.id, task_id=t.id, status='In Progress')
                    db.session.add(new_ut)
                db.session.commit()
                today_tasks = UserTask.query.filter(
                    UserTask.user_id == current_user.id,
                    db.func.date(UserTask.date_accepted) == today
                ).all()

        return render_template('daily_tasks.html', title='Daily Quests', today_tasks=today_tasks)

    @app.route('/submit_proof/<int:user_task_id>', methods=['POST'])
    @login_required
    def submit_proof(user_task_id):
        user_task = UserTask.query.get_or_404(user_task_id)
        if user_task.user_id != current_user.id:
            flash('Unauthorized action.', 'danger')
            return redirect(url_for('daily_tasks'))

        if 'proof_image' in request.files:
            file = request.files['proof_image']
            if file.filename != '':
                picture_file = save_picture(file)
                user_task.proof_image = picture_file
                user_task.status = 'Pending Review' if user_task.task.proof_required else 'Completed'
                db.session.commit()

                # Check if they finished all 3 tasks today
                today = date.today()
                all_today = UserTask.query.filter(
                    UserTask.user_id == current_user.id,
                    db.func.date(UserTask.date_accepted) == today
                ).all()

                if all(ut.status in ['Completed', 'Pending Review'] for ut in all_today):
                    base_points = 50
                    source_label = "Daily Tasks"
                    
                    # STREAK MULTIPLIER LOGIC
                    user_streak = Streak.query.filter_by(user_id=current_user.id).first()
                    if user_streak and user_streak.current_streak >= 7:
                        base_points = int(base_points * 1.5) # 50% Bonus
                        source_label = "Daily Tasks (7-Day Streak Bonus)"
                    
                    award_points(current_user.id, base_points, source_label)
                    current_user.points += base_points
                    current_user.streak += 1
                    db.session.commit()
                    flash(f'All daily tasks finished! +{base_points} Points logged!', 'success')
                else:
                    flash('Task submitted! Keep going.', 'info')
        return redirect(url_for('daily_tasks'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)