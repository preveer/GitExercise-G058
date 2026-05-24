import os
import secrets
import random
from datetime import date, datetime, timedelta

from flask import Flask, abort, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from models import (Task, db, login_manager, User, Badge, Event,
                    RSVP, UserTask, Challenge, Submission, Point)
from forms import (BadgeForm, RegistrationForm, LoginForm, EventForm,
                   ChangePasswordForm, UpdateProfileForm, TaskForm, ChallengeForm,
                   ForgotPasswordForm, ResetPasswordForm)
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        db.create_all()

    # ------------------------------------------------------------------ #
    # HELPER FUNCTIONS
    # ------------------------------------------------------------------ #

    def save_picture(form_picture):
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(app.root_path, 'static', 'profile_pics', picture_fn)
        os.makedirs(os.path.dirname(picture_path), exist_ok=True)
        form_picture.save(picture_path)
        return picture_fn

    def save_upload(form_file):
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_file.filename)
        file_fn = random_hex + f_ext
        file_path = os.path.join(app.root_path, 'static', 'uploads', file_fn)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        form_file.save(file_path)
        return file_fn

    def award_points(user_id, amount, source):
        """Creates a Point log entry. Caller must commit."""
        new_point = Point(user_id=user_id, amount=amount, source=source)
        db.session.add(new_point)

    def check_and_award_badges(user):
        """Checks user stats and awards badges they have earned."""
        if user.streak >= 7:
            streak_badge = Badge.query.filter_by(title='Streak Master').first()
            if streak_badge and streak_badge not in user.badges:
                user.badges.append(streak_badge)
                flash("You've earned the Streak Master badge!", 'warning')

    # ------------------------------------------------------------------ #
    # MAIN ROUTES
    # ------------------------------------------------------------------ #

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
            hashed_password = generate_password_hash(form.password.data)
            user = User(
                name=form.name.data,
                email=form.email.data,
                password=hashed_password,
                faculty=form.faculty.data,
            )
            if form.sport_preferences.data:
                user.sport_preferences = form.sport_preferences.data
            if form.picture.data and form.picture.data.filename:
                user.profile_photo = save_picture(form.picture.data)
            db.session.add(user)
            db.session.commit()
            flash('Account created! Welcome to the Titan Arena — please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                if user.is_banned:
                    flash('Your account has been banned by an administrator.', 'danger')
                    return redirect(url_for('login'))
                login_user(user, remember=form.remember.data)
                flash('Welcome back to the Titan Arena!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Login unsuccessful. Please check your email and password.', 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    # ------------------------------------------------------------------ #
    # FORGOT / RESET PASSWORD ROUTES
    # ------------------------------------------------------------------ #

    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = ForgotPasswordForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                token = secrets.token_urlsafe(32)
                user.reset_token = token
                user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
                db.session.commit()
                reset_url = url_for('reset_password', token=token, _external=True)
                flash(
                    f'Reset link generated! Copy this link and open it in your browser: {reset_url}',
                    'info'
                )
            else:
                flash('If that email is registered, a reset link has been generated.', 'info')
            return redirect(url_for('forgot_password'))
        return render_template('forgot_password.html', title='Forgot Password', form=form)

    @app.route('/reset_password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        user = User.query.filter_by(reset_token=token).first()
        if not user or user.reset_token_expiry < datetime.utcnow():
            flash('That reset link is invalid or has expired. Please request a new one.', 'danger')
            return redirect(url_for('forgot_password'))
        form = ResetPasswordForm()
        if form.validate_on_submit():
            user.password = generate_password_hash(form.new_password.data)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Your password has been reset! You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('reset_password.html', title='Reset Password', form=form)

    # ------------------------------------------------------------------ #
    # ADMIN ROUTES
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # ADMIN - BADGE ROUTES
    # ------------------------------------------------------------------ #

    @app.route('/admin/badges')
    @login_required
    def admin_badges():
        if not current_user.is_admin:
            abort(403)
        badges = Badge.query.all()
        return render_template('admin_badges.html', badges=badges, title="Manage Badges")

    @app.route('/admin/badges/new', methods=['GET', 'POST'])
    @login_required
    def add_badge():
        if not current_user.is_admin:
            abort(403)
        form = BadgeForm()
        if form.validate_on_submit():
            badge = Badge(
                title=form.title.data,
                description=form.description.data,
                category=form.category.data
            )
            db.session.add(badge)
            db.session.commit()
            flash('New badge has been created!', 'success')
            return redirect(url_for('admin_badges'))
        return render_template('admin_badge_form.html', title='New Badge',
                               form=form, legend='Create New Badge')

    @app.route('/admin/badges/<int:badge_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_badge(badge_id):
        if not current_user.is_admin:
            abort(403)
        badge = Badge.query.get_or_404(badge_id)
        form = BadgeForm()
        if form.validate_on_submit():
            badge.title = form.title.data
            badge.description = form.description.data
            badge.category = form.category.data
            db.session.commit()
            flash('Badge has been updated!', 'success')
            return redirect(url_for('admin_badges'))
        elif request.method == 'GET':
            form.title.data = badge.title
            form.description.data = badge.description
            form.category.data = badge.category
        return render_template('admin_badge_form.html', title='Edit Badge',
                               form=form, legend='Edit Badge')

    @app.route('/admin/badges/<int:badge_id>/delete', methods=['POST'])
    @login_required
    def delete_badge(badge_id):
        if not current_user.is_admin:
            abort(403)
        badge = Badge.query.get_or_404(badge_id)
        db.session.delete(badge)
        db.session.commit()
        flash('Badge has been deleted.', 'info')
        return redirect(url_for('admin_badges'))

    # ------------------------------------------------------------------ #
    # ADMIN - SUBMISSION VERIFICATION
    # ------------------------------------------------------------------ #

    @app.route('/admin/submissions/<int:submission_id>/verify', methods=['POST'])
    @login_required
    def verify_submission(submission_id):
        if not current_user.is_admin:
            abort(403)
        submission = Submission.query.get_or_404(submission_id)
        if not submission.verified:
            submission.verified = True
            student = User.query.get(submission.user_id)
            student.points += 50
            award_points(student.id, 50,
                         f"Challenge Verified: {submission.challenge_ref.title}")
            top_3_users = User.query.order_by(User.points.desc()).limit(3).all()
            if student in top_3_users:
                winner_badge = Badge.query.filter_by(title='Weekly Winner').first()
                if winner_badge and winner_badge not in student.badges:
                    student.badges.append(winner_badge)
                    flash(f"{student.name} is in the Top 3 and earned the Weekly Winner badge!",
                          'warning')
            db.session.commit()
            flash('Submission verified and 50 points awarded!', 'success')
        else:
            flash('This submission was already verified.', 'info')
        return redirect(url_for('view_submissions',
                                challenge_id=submission.challenge_id))

    # ------------------------------------------------------------------ #
    # PROFILE ROUTES
    # ------------------------------------------------------------------ #

    @app.route('/profile')
    @login_required
    def profile():
        point_history = (Point.query
                         .filter_by(user_id=current_user.id)
                         .order_by(Point.awarded_at.desc())
                         .all())
        return render_template('profile.html', title='My Profile',
                               user=current_user, point_history=point_history)

    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        form = UpdateProfileForm()
        if form.validate_on_submit():
            if form.picture.data and form.picture.data.filename:
                current_user.profile_photo = save_picture(form.picture.data)
            current_user.name = form.name.data
            current_user.email = form.email.data
            current_user.faculty = form.faculty.data
            current_user.sport_preferences = form.sport_preferences.data
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.name.data = current_user.name
            form.email.data = current_user.email
            form.faculty.data = current_user.faculty
            form.sport_preferences.data = current_user.sport_preferences
        return render_template('edit_profile.html', title='Edit Profile', form=form)

    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if not check_password_hash(current_user.password, form.old_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('change_password.html',
                                       title='Change Password', form=form)
            current_user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('profile'))
        return render_template('change_password.html',
                               title='Change Password', form=form)

    @app.route('/my_badges')
    @login_required
    def my_badges():
        all_badges = Badge.query.all()
        return render_template('badges.html', all_badges=all_badges,
                               title="My Achievements")

    # ------------------------------------------------------------------ #
    # EVENT ROUTES
    # ------------------------------------------------------------------ #

    @app.route('/admin/events', methods=['GET', 'POST'])
    @login_required
    def manage_events():
        if not current_user.is_admin:
            flash('Access Denied.', 'danger')
            return redirect(url_for('home'))
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

    @app.route('/events')
    @login_required
    def list_events():
        events = Event.query.all()
        user_rsvps = {rsvp.event_id: rsvp for rsvp in
                      RSVP.query.filter_by(user_id=current_user.id).all()}
        spots_left = {}
        for event in events:
            confirmed_count = RSVP.query.filter_by(
                event_id=event.id, waitlisted=False).count()
            spots_left[event.id] = event.max_capacity - confirmed_count
        return render_template('events.html', events=events,
                               user_rsvps=user_rsvps, spots_left=spots_left)

    @app.route('/events/<int:event_id>/rsvp', methods=['POST'])
    @login_required
    def rsvp(event_id):
        event = Event.query.get_or_404(event_id)
        existing = RSVP.query.filter_by(user_id=current_user.id,
                                        event_id=event_id).first()
        if existing:
            flash("You have already RSVP'd for this event.", 'info')
            return redirect(url_for('list_events'))
        confirmed_count = RSVP.query.filter_by(event_id=event_id,
                                               waitlisted=False).count()
        waitlisted = confirmed_count >= event.max_capacity
        new_rsvp = RSVP(user_id=current_user.id, event_id=event_id,
                        waitlisted=waitlisted)
        db.session.add(new_rsvp)
        db.session.commit()
        if waitlisted:
            flash('Event is full. You have been added to the waitlist.', 'warning')
        else:
            flash('RSVP confirmed! See you there.', 'success')
        return redirect(url_for('list_events'))

    @app.route('/events/<int:event_id>/cancel', methods=['POST'])
    @login_required
    def cancel_rsvp(event_id):
        rsvp_entry = RSVP.query.filter_by(user_id=current_user.id,
                                          event_id=event_id).first_or_404()
        db.session.delete(rsvp_entry)
        db.session.commit()
        first_waitlisted = RSVP.query.filter_by(event_id=event_id,
                                                 waitlisted=True).first()
        if first_waitlisted:
            first_waitlisted.waitlisted = False
            db.session.commit()
            flash('RSVP cancelled. A waitlisted user has been promoted.', 'info')
        else:
            flash('Your RSVP has been cancelled.', 'info')
        return redirect(url_for('list_events'))

    @app.route('/events/<int:event_id>/checkin', methods=['POST'])
    @login_required
    def checkin(event_id):
        rsvp_entry = RSVP.query.filter_by(user_id=current_user.id,
                                          event_id=event_id,
                                          waitlisted=False).first()
        if rsvp_entry and not rsvp_entry.checked_in:
            rsvp_entry.checked_in = True
            current_user.points += 50
            award_points(current_user.id, 50, "Event Check-In")
            event_badge = Badge.query.filter_by(title='Event Goer').first()
            if not event_badge:
                event_badge = Badge(title='Event Goer',
                                    description='Attended a campus sporting event',
                                    category="Event")
                db.session.add(event_badge)
            if event_badge not in current_user.badges:
                current_user.badges.append(event_badge)
            db.session.commit()
            flash('Checked in! +50 Points and Badge earned!', 'success')
        else:
            flash('Check-in failed. You must have a confirmed spot.', 'danger')
        return redirect(url_for('list_events'))

    # ------------------------------------------------------------------ #
    # TASK ROUTES
    # ------------------------------------------------------------------ #

    @app.route('/admin/tasks')
    @login_required
    def admin_tasks():
        if not current_user.is_admin:
            flash('Access Denied.', 'danger')
            return redirect(url_for('home'))
        tasks = Task.query.all()
        return render_template('admin_tasks.html', tasks=tasks)

    @app.route('/admin/tasks/add', methods=['GET', 'POST'])
    @login_required
    def add_task():
        if not current_user.is_admin:
            return redirect(url_for('home'))
        form = TaskForm()
        if form.validate_on_submit():
            new_task = Task(
                title=form.title.data,
                description=form.description.data,
                sport_category=form.sport_category.data,
                difficulty=form.difficulty.data,
                proof_required=form.proof_required.data
            )
            db.session.add(new_task)
            db.session.commit()
            flash('New task added!', 'success')
            return redirect(url_for('admin_tasks'))
        return render_template('admin_task_form.html', form=form, legend='Add New Task')

    @app.route('/admin/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
    @login_required
    def edit_task(task_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        task = Task.query.get_or_404(task_id)
        form = TaskForm()
        if form.validate_on_submit():
            task.title = form.title.data
            task.description = form.description.data
            task.sport_category = form.sport_category.data
            task.difficulty = form.difficulty.data
            task.proof_required = form.proof_required.data
            db.session.commit()
            flash('Task updated!', 'success')
            return redirect(url_for('admin_tasks'))
        elif request.method == 'GET':
            form.title.data = task.title
            form.description.data = task.description
            form.sport_category.data = task.sport_category
            form.difficulty.data = task.difficulty
            form.proof_required.data = task.proof_required
        return render_template('admin_task_form.html', form=form, legend='Edit Task')

    @app.route('/admin/tasks/delete/<int:task_id>', methods=['POST'])
    @login_required
    def delete_task(task_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        task = Task.query.get_or_404(task_id)
        UserTask.query.filter_by(task_id=task.id).delete()
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted.', 'info')
        return redirect(url_for('admin_tasks'))

    @app.route('/daily_tasks')
    @login_required
    def daily_tasks():
        today = date.today()
        today_tasks = UserTask.query.filter(
            UserTask.user_id == current_user.id,
            db.func.date(UserTask.date_accepted) == today
        ).all()
        if len(today_tasks) == 0:
            if current_user.sport_preferences:
                pool = Task.query.filter(
                    Task.sport_category.ilike(
                        f"%{current_user.sport_preferences}%")
                ).all()
            else:
                pool = Task.query.all()
            if len(pool) < 3:
                pool = Task.query.all()
            if len(pool) > 0:
                chosen_tasks = random.sample(pool, min(3, len(pool)))
                for t in chosen_tasks:
                    new_ut = UserTask(user_id=current_user.id,
                                      task_id=t.id, status='In Progress')
                    db.session.add(new_ut)
                db.session.commit()
                today_tasks = UserTask.query.filter(
                    UserTask.user_id == current_user.id,
                    db.func.date(UserTask.date_accepted) == today
                ).all()
        return render_template('daily_tasks.html', title='Daily Quests',
                               today_tasks=today_tasks)

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
        user_task.status = ('Pending Review'
                            if user_task.task_ref.proof_required
                            else 'Completed')
        db.session.commit()
        today = date.today()
        all_today = UserTask.query.filter(
            UserTask.user_id == current_user.id,
            db.func.date(UserTask.date_accepted) == today
        ).all()
        if all(ut.status in ['Completed', 'Pending Review'] for ut in all_today):
            base_points = 50
            source_label = "Daily Tasks"
            if current_user.streak >= 7:
                base_points = int(base_points * 1.5)
                source_label = "Daily Tasks (7-Day Streak Bonus)"
            award_points(current_user.id, base_points, source_label)
            current_user.points += base_points
            current_user.streak += 1
            check_and_award_badges(current_user)
            db.session.commit()
            flash(f'All daily tasks finished! +{base_points} Points and streak continues!',
                  'success')
        else:
            flash('Task submitted! Keep going to finish your daily 3.', 'info')
        return redirect(url_for('daily_tasks'))

    @app.route('/task/<int:utask_id>/complete', methods=['POST'])
    @login_required
    def complete_task(utask_id):
        utask = UserTask.query.get_or_404(utask_id)
        if utask.user_id != current_user.id:
            abort(403)
        utask.status = 'Completed'
        current_user.points += 10
        current_user.streak += 1
        award_points(current_user.id, 10, f"Task: {utask.task_ref.title}")
        check_and_award_badges(current_user)
        db.session.commit()
        flash('Task completed! +10 Points and Streak Up!', 'success')
        return redirect(url_for('daily_tasks'))

    # ------------------------------------------------------------------ #
    # CHALLENGE ROUTES (Admin)
    # ------------------------------------------------------------------ #

    @app.route('/admin/challenges')
    @login_required
    def admin_challenges():
        if not current_user.is_admin:
            flash('Access denied.', 'danger')
            return redirect(url_for('home'))
        challenges = Challenge.query.all()
        return render_template('admin_challenges.html',
                               title='Manage Challenges', challenges=challenges)

    @app.route('/admin/challenges/add', methods=['GET', 'POST'])
    @login_required
    def add_challenge():
        if not current_user.is_admin:
            return redirect(url_for('home'))
        form = ChallengeForm()
        if form.validate_on_submit():
            new_challenge = Challenge(
                title=form.title.data,
                description=form.description.data,
                sport_category=form.sport_category.data,
                deadline=datetime.combine(form.deadline.data, datetime.min.time()),
                scoring_criteria=form.scoring_criteria.data
            )
            db.session.add(new_challenge)
            db.session.commit()
            flash('New weekly challenge created!', 'success')
            return redirect(url_for('admin_challenges'))
        return render_template('admin_challenge_form.html',
                               title='Add Challenge', form=form,
                               legend='Create New Challenge')

    @app.route('/admin/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
    @login_required
    def edit_challenge(challenge_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        challenge = Challenge.query.get_or_404(challenge_id)
        form = ChallengeForm()
        if form.validate_on_submit():
            challenge.title = form.title.data
            challenge.description = form.description.data
            challenge.sport_category = form.sport_category.data
            challenge.deadline = datetime.combine(form.deadline.data,
                                                   datetime.min.time())
            challenge.scoring_criteria = form.scoring_criteria.data
            db.session.commit()
            flash('Challenge updated!', 'success')
            return redirect(url_for('admin_challenges'))
        elif request.method == 'GET':
            form.title.data = challenge.title
            form.description.data = challenge.description
            form.sport_category.data = challenge.sport_category
            form.deadline.data = (challenge.deadline.date()
                                  if challenge.deadline else None)
            form.scoring_criteria.data = challenge.scoring_criteria
        return render_template('admin_challenge_form.html',
                               title='Edit Challenge', form=form,
                               legend='Edit Challenge')

    @app.route('/admin/challenges/delete/<int:challenge_id>', methods=['POST'])
    @login_required
    def delete_challenge(challenge_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        challenge = Challenge.query.get_or_404(challenge_id)
        db.session.delete(challenge)
        db.session.commit()
        flash('Challenge deleted.', 'info')
        return redirect(url_for('admin_challenges'))

    @app.route('/admin/challenges/<int:challenge_id>/submissions')
    @login_required
    def view_submissions(challenge_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        challenge = Challenge.query.get_or_404(challenge_id)
        submissions = Submission.query.filter_by(challenge_id=challenge.id).all()
        return render_template('admin_submissions.html',
                               title='View Submissions',
                               challenge=challenge, submissions=submissions)

    @app.route('/admin/challenges/<int:challenge_id>/close', methods=['POST'])
    @login_required
    def close_challenge(challenge_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        challenge = Challenge.query.get_or_404(challenge_id)
        challenge.is_closed = True
        db.session.commit()
        flash('Challenge is now closed for new submissions!', 'info')
        return redirect(url_for('admin_challenges'))

    # ------------------------------------------------------------------ #
    # STUDENT CHALLENGE ROUTES
    # ------------------------------------------------------------------ #

    @app.route('/challenges')
    @login_required
    def student_challenges():
        challenges = Challenge.query.all()
        return render_template('student_challenges.html',
                               title='Weekly Challenges', challenges=challenges)

    @app.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
    @login_required
    def challenge_detail(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        existing_submission = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id
        ).first()
        if (request.method == 'POST'
                and not challenge.is_closed
                and not existing_submission):
            result = request.form.get('result')
            proof = request.files.get('proof_file')
            if proof and result:
                file_fn = save_upload(proof)
                new_submission = Submission(
                    user_id=current_user.id,
                    challenge_id=challenge_id,
                    result=result,
                    proof_file=file_fn
                )
                db.session.add(new_submission)
                db.session.commit()
                flash('Your attempt has been submitted! Good luck!', 'success')
                return redirect(url_for('challenge_detail',
                                        challenge_id=challenge_id))
            else:
                flash('Please fill in your result and upload a proof image.', 'danger')
        submissions = Submission.query.filter_by(challenge_id=challenge_id).all()
        return render_template('challenge_detail.html',
                               challenge=challenge,
                               existing_submission=existing_submission,
                               submissions=submissions)

    # ------------------------------------------------------------------ #
    # LEADERBOARD ROUTE
    # ------------------------------------------------------------------ #

    @app.route('/leaderboard')
    @login_required
    def leaderboard():
        selected_faculty = request.args.get('faculty', '')
        selected_sport = request.args.get('sport', '')

        faculties = [u[0] for u in db.session.query(User.faculty).distinct().all() if u[0]]
        sports = [u[0] for u in db.session.query(User.sport_preferences).distinct().all() if u[0]]

        base_query = User.query.filter_by(is_admin=False)

        if selected_faculty:
            base_query = base_query.filter_by(faculty=selected_faculty)

        if selected_sport:
            base_query = base_query.filter(User.sport_preferences.ilike(f'%{selected_sport}%'))

        points_users = base_query.order_by(User.points.desc()).all()
        streak_users = base_query.order_by(User.streak.desc()).all()

        return render_template('leaderboard.html',
                               points_users=points_users,
                               streak_users=streak_users,
                               faculties=faculties,
                               sports=sports,
                               selected_faculty=selected_faculty,
                               selected_sport=selected_sport,
                               title="Leaderboard")

    @app.route("/admin/reset_season", methods=['POST'])
    @login_required
    def reset_season():
        if not current_user.is_admin:
            abort(403)
        students = User.query.filter_by(is_admin=False).all()
        for student in students:
            student.points = 0
            student.streak = 0
        db.session.commit()
        flash('The season has been reset. All student rankings are now at zero.', 'warning')
        return redirect(url_for('admin_dashboard'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)