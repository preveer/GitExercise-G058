import os
import secrets
import random
from datetime import date, datetime
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required

from models import db, login_manager, User, Badge, Event, RSVP, Task, UserTask, Point, Streak, Submission, Challenge
from forms import RegistrationForm, LoginForm, EventForm, ChangePasswordForm, UpdateProfileForm, TaskForm
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
        new_point = Point(user_id=user_id, amount=amount, source=source)
        db.session.add(new_point)

    # --- MAIN ROUTES ---
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
                if user.is_banned:
                    flash('Your account has been banned by an administrator.', 'danger')
                    return redirect(url_for('login'))
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

    # --- LUTHRA'S WEEK 6: ADMIN BACKEND PANEL ---
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if not current_user.is_admin:
            flash('Access Denied. Admins only.', 'danger')
            return redirect(url_for('home'))
        
        total_users = User.query.count()
        total_tasks = Task.query.count()
        total_events = Event.query.count()
        pending_submissions = Submission.query.filter_by(verified=False).count()
        
        return render_template('admin_dashboard.html', 
                               total_users=total_users, 
                               total_tasks=total_tasks, 
                               total_events=total_events, 
                               pending_submissions=pending_submissions)

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if not current_user.is_admin:
            flash('Access Denied.', 'danger')
            return redirect(url_for('home'))
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/users/<int:user_id>/ban', methods=['POST'])
    @login_required
    def ban_user(user_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash("You cannot ban yourself!", "danger")
        else:
            user.is_banned = not user.is_banned
            db.session.commit()
            status = "banned" if user.is_banned else "unbanned"
            flash(f"User {user.name} has been {status}.", "success")
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    def delete_user(user_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash("You cannot delete yourself!", "danger")
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f"User {user.name} has been permanently deleted.", "success")
        return redirect(url_for('admin_users'))

    # --- PROFILE ROUTES ---
    @app.route('/profile')
    @login_required
    def profile():
        point_history = Point.query.filter_by(user_id=current_user.id).order_by(Point.awarded_at.desc()).all()
        return render_template('profile.html', title='My Profile', user=current_user, point_history=point_history)

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
            current_user.password = form.new_password.data
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('profile'))
        return render_template('change_password.html', title='Change Password', form=form)

    @app.route('/my_badges')
    @login_required
    def my_badges():
        return render_template('badges.html', title='My Badges', badges=current_user.badges)

    # --- EVENT ROUTES ---
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

    @app.route('/checkin/<int:event_id>', methods=['POST'])
    @login_required
    def checkin(event_id):
        rsvp = RSVP.query.filter_by(user_id=current_user.id, event_id=event_id).first()
        if rsvp and not rsvp.waitlisted and not rsvp.checked_in:
            rsvp.checked_in = True
            award_points(current_user.id, 50, f"Event Attendance: {event_id}")
            current_user.points += 50
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

    # --- TASK ROUTES ---
    @app.route('/tasks')
    @login_required
    def daily_tasks():
        tasks = Task.query.all()
        user_tasks = UserTask.query.filter_by(user_id=current_user.id).all()
        return render_template('daily_tasks.html', title='Daily Quests', tasks=tasks, user_tasks=user_tasks)

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
        
        # Streak and Point Logic
        today = date.today()
        all_today = UserTask.query.filter(UserTask.user_id == current_user.id, 
                                          db.func.date(UserTask.date_accepted) == today).all()
        if all(ut.status in ['Completed', 'Pending Review'] for ut in all_today):
            base_points = 50
            source_label = "Daily Tasks"
            user_streak = Streak.query.filter_by(user_id=current_user.id).first()
            if user_streak and user_streak.current_streak >= 7:
                base_points = int(base_points * 1.5)
                source_label = "Daily Tasks (7-Day Streak Bonus)"
            award_points(current_user.id, base_points, source_label)
            current_user.points += base_points
            current_user.streak += 1
            db.session.commit()
            flash(f'All daily tasks finished! +{base_points} Points logged!', 'success')
        return redirect(url_for('daily_tasks'))

    @app.route('/admin/verify_challenge/<int:submission_id>/<int:rank>', methods=['POST'])
    @login_required
    def verify_challenge(submission_id, rank):
        if not current_user.is_admin:
            flash('Access denied.', 'danger')
            return redirect(url_for('home'))
        submission = Submission.query.get_or_404(submission_id)
        points_map = {1: 150, 2: 100, 3: 50}
        reward = points_map.get(rank, 0)
        if not submission.verified:
            submission.verified = True
            award_points(submission.user_id, reward, f"Challenge Rank {rank} Bonus")
            submission.user.points += reward
            db.session.commit()
            flash(f'Verified! {reward} points awarded.', 'success')
        return redirect(url_for('admin_dashboard'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)