import os
import secrets
import random
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, abort, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from models import (Task, db, login_manager, User, Event,
                    RSVP, UserTask, Challenge, Submission, Point,
                    Feedback, BuddyRequest)
from forms import (RegistrationForm, LoginForm, EventForm,
                   ChangePasswordForm, UpdateProfileForm, TaskForm,
                   ChallengeForm, ForgotPasswordForm, ResetPasswordForm, FeedbackForm,
                   BuddyAvailabilityForm)
from config import Config


# ------------------------------------------------------------------
# ADMIN DECORATOR  (Reduction 1 — replaces ~15 repeated if-blocks)
# ------------------------------------------------------------------

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access Denied. Admins only.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    with app.app_context():
        db.create_all()

    # ------------------------------------------------------------------
    # HELPER FUNCTIONS
    # ------------------------------------------------------------------

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

    def check_daily_completion(user):
        """Checks if all 3 daily tasks are Complete and awards the 50 points."""
        today = date.today()
        all_today = UserTask.query.filter(
            UserTask.user_id == user.id,
            db.func.date(UserTask.date_accepted) == today
        ).all()

        if len(all_today) == 3 and all(ut.status == 'Completed' for ut in all_today):
            already_awarded = Point.query.filter(
                Point.user_id == user.id,
                Point.source.like('Daily Tasks%'),
                db.func.date(Point.awarded_at) == today
            ).first()

            if not already_awarded:
                base_points = 50
                source_label = "Daily Tasks"
                if user.streak >= 7:
                    base_points = int(base_points * 1.5)
                    source_label = "Daily Tasks (7-Day Streak Bonus)"

                award_points(user.id, base_points, source_label)
                user.points += base_points
                user.streak += 1
                db.session.commit()
                return base_points
        return 0

    # ------------------------------------------------------------------
    # MAIN ROUTES
    # ------------------------------------------------------------------

    @app.route('/')
    def home():
        if current_user.is_authenticated:
            # --- AAHTITIYA'S WEEK 8: MONDAY WINNER ANNOUNCEMENT ---
            # Python's weekday() returns 0 for Monday, 1 for Tuesday, etc.
            is_monday = date.today().weekday() == 0
            recent_closed_challenge = None
            top_winners = []
            
            # If today is Monday, fetch the latest closed challenge and its top 3 verified winners
            if is_monday:
                recent_closed_challenge = Challenge.query.filter_by(is_closed=True).order_by(Challenge.deadline.desc()).first()
                if recent_closed_challenge:
                    top_winners = Submission.query.filter_by(
                        challenge_id=recent_closed_challenge.id, 
                        verified=True
                    ).limit(3).all()

            return render_template('dashboard.html', 
                                   title='Dashboard', 
                                   is_monday=is_monday, 
                                   recent_challenge=recent_closed_challenge, 
                                   winners=top_winners)
            
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
            admin_emails = ['preveeradmin@gmail.com', 'luthraadmin@gmail.com', 'aahtiadmin@gmail.com']
            if user.email.lower() in admin_emails:
                user.is_admin = True
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

    # ------------------------------------------------------------------
    # FORGOT / RESET PASSWORD ROUTES
    # ------------------------------------------------------------------

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
                flash(f'Reset link generated! Copy this link and open it in your browser: {reset_url}', 'info')
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

    # ------------------------------------------------------------------
    # ADMIN ROUTES
    # ------------------------------------------------------------------

    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        # Bug 6 fix: removed unused total_tasks query
        total_users = User.query.count()
        total_events = Event.query.count()
        pending_submissions = Submission.query.filter_by(verified=False).count()
        return render_template('admin_dashboard.html',
                               total_users=total_users,
                               total_events=total_events,
                               pending_submissions=pending_submissions)

    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/users/<int:user_id>/ban', methods=['POST'])
    @login_required
    @admin_required
    def ban_user(user_id):
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
    @admin_required
    def delete_user(user_id):
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash("You cannot delete yourself!", "danger")
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f"User {user.name} has been permanently deleted.", "success")
        return redirect(url_for('admin_users'))

    # ------------------------------------------------------------------
    # ADMIN - SUBMISSION VERIFICATION  (Bug 4 fix: save challenge_id before delete)
    # ------------------------------------------------------------------

    @app.route('/admin/submissions/<int:submission_id>/<string:action>', methods=['POST'])
    @login_required
    @admin_required
    def verify_submission(submission_id, action):
        submission = Submission.query.get_or_404(submission_id)
        challenge_id = submission.challenge_id  # Save before any deletion

        if action == 'approve':
            submission.verified = True
            student = User.query.get(submission.user_id)
            student.points += 50
            award_points(student.id, 50, f"Challenge Verified: {submission.challenge_ref.title}")
            db.session.commit()
            flash(f"Submission approved! 50 points awarded to {student.name}.", "success")

        elif action == 'reject':
            db.session.delete(submission)
            db.session.commit()
            flash("Submission has been rejected and removed.", "warning")

        return redirect(url_for('view_submissions', challenge_id=challenge_id))

    # ------------------------------------------------------------------
    # PROFILE ROUTES
    # ------------------------------------------------------------------

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
                return render_template('change_password.html', title='Change Password', form=form)
            current_user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('profile'))
        return render_template('change_password.html', title='Change Password', form=form)

    # ------------------------------------------------------------------
    # EVENT ROUTES
    # ------------------------------------------------------------------

    @app.route('/admin/events', methods=['GET', 'POST'])
    @login_required
    @admin_required
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

    @app.route('/events/<int:event_id>/rsvp', methods=['POST'])
    @login_required
    def rsvp(event_id):
        event = Event.query.get_or_404(event_id)
        existing = RSVP.query.filter_by(user_id=current_user.id, event_id=event_id).first()
        if existing:
            flash("You have already RSVP'd for this event.", 'info')
            return redirect(url_for('list_events'))
        confirmed_count = RSVP.query.filter_by(event_id=event_id, waitlisted=False).count()
        waitlisted = confirmed_count >= event.max_capacity
        new_rsvp = RSVP(user_id=current_user.id, event_id=event_id, waitlisted=waitlisted)
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
        rsvp_entry = RSVP.query.filter_by(user_id=current_user.id, event_id=event_id).first_or_404()
        db.session.delete(rsvp_entry)
        db.session.commit()
        first_waitlisted = RSVP.query.filter_by(event_id=event_id, waitlisted=True).first()
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
        rsvp_entry = RSVP.query.filter_by(user_id=current_user.id, event_id=event_id, waitlisted=False).first()
        if rsvp_entry and not rsvp_entry.checked_in:
            rsvp_entry.checked_in = True
            current_user.points += 50
            award_points(current_user.id, 50, "Event Check-In")
            db.session.commit()
            flash('Checked in! +50 Points earned!', 'success')
        else:
            flash('Check-in failed. You must have a confirmed spot.', 'danger')
        return redirect(url_for('list_events'))

    # ------------------------------------------------------------------
    # TASK ROUTES
    # ------------------------------------------------------------------

    @app.route('/admin/tasks')
    @login_required
    @admin_required
    def admin_tasks():
        tasks = Task.query.all()
        return render_template('admin_tasks.html', tasks=tasks)

    @app.route('/admin/tasks/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def add_task():
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
    @admin_required
    def edit_task(task_id):
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
    @admin_required
    def delete_task(task_id):
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
                pool = Task.query.filter(Task.sport_category.ilike(f"%{current_user.sport_preferences}%")).all()
            else:
                pool = Task.query.all()
            if len(pool) < 3:
                pool = Task.query.all()
            if len(pool) > 0:
                chosen_tasks = random.sample(pool, min(3, len(pool)))
                for t in chosen_tasks:
                    # FIXED: Explicitly set date_accepted to match local server date
                    new_ut = UserTask(
                        user_id=current_user.id, 
                        task_id=t.id, 
                        status='In Progress',
                        date_accepted=today
                )
                    db.session.add(new_ut)
                db.session.commit()
                today_tasks = UserTask.query.filter(
                    UserTask.user_id == current_user.id,
                    db.func.date(UserTask.date_accepted) == today
                ).all()
        return render_template('daily_tasks.html', title='Daily Quests', today_tasks=today_tasks)

    # Bug 3 fix: "Mark as Done" was silently doing nothing for non-proof tasks
    @app.route('/submit_proof/<int:user_task_id>', methods=['POST'])
    @login_required
    def submit_proof(user_task_id):
        user_task = UserTask.query.get_or_404(user_task_id)
        if user_task.user_id != current_user.id:
            flash('Unauthorized action.', 'danger')
            return redirect(url_for('daily_tasks'))

        if user_task.task_ref.proof_required:
            file = request.files.get('proof_image')
            if file and file.filename != '':
                user_task.proof_image = save_picture(file)
                user_task.status = 'Pending Review'
                db.session.commit()
                flash('Photo submitted! Awaiting admin approval.', 'info')
            else:
                flash('Please upload a proof image.', 'danger')
        else:
            # No proof needed — mark complete immediately
            user_task.status = 'Completed'
            current_user.points += 10
            award_points(current_user.id, 10, f"Task: {user_task.task_ref.title}")
            bonus = check_daily_completion(current_user)
            db.session.commit()
            if bonus:
                flash(f'Task done! All daily tasks finished! +{bonus} Bonus Points!', 'success')
            else:
                flash('Task completed! +10 Points!', 'success')

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
        db.session.commit()
        flash('Task completed! +10 Points and Streak Up!', 'success')
        return redirect(url_for('daily_tasks'))

    # ------------------------------------------------------------------
    # CHALLENGE ROUTES (Admin)
    # ------------------------------------------------------------------

    @app.route('/admin/challenges')
    @login_required
    @admin_required
    def admin_challenges():
        challenges = Challenge.query.all()
        return render_template('admin_challenges.html', title='Manage Challenges', challenges=challenges)

    @app.route('/admin/challenges/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def add_challenge():
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
        return render_template('admin_challenge_form.html', title='Add Challenge', form=form, legend='Create New Challenge')

    @app.route('/admin/challenges/edit/<int:challenge_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_challenge(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        form = ChallengeForm()
        if form.validate_on_submit():
            challenge.title = form.title.data
            challenge.description = form.description.data
            challenge.sport_category = form.sport_category.data
            challenge.deadline = datetime.combine(form.deadline.data, datetime.min.time())
            challenge.scoring_criteria = form.scoring_criteria.data
            db.session.commit()
            flash('Challenge updated!', 'success')
            return redirect(url_for('admin_challenges'))
        elif request.method == 'GET':
            form.title.data = challenge.title
            form.description.data = challenge.description
            form.sport_category.data = challenge.sport_category
            form.deadline.data = (challenge.deadline.date() if challenge.deadline else None)
            form.scoring_criteria.data = challenge.scoring_criteria
        return render_template('admin_challenge_form.html', title='Edit Challenge', form=form, legend='Edit Challenge')

    @app.route('/admin/challenges/delete/<int:challenge_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_challenge(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        db.session.delete(challenge)
        db.session.commit()
        flash('Challenge deleted.', 'info')
        return redirect(url_for('admin_challenges'))

    @app.route('/admin/challenges/<int:challenge_id>/submissions')
    @login_required
    @admin_required
    def view_submissions(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        submissions = Submission.query.filter_by(challenge_id=challenge.id).all()
        return render_template('admin_submissions.html', title='View Submissions', challenge=challenge, submissions=submissions)

    @app.route('/admin/challenges/<int:challenge_id>/close', methods=['POST'])
    @login_required
    @admin_required
    def close_challenge(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
        challenge.is_closed = True
        db.session.commit()
        flash('Challenge is now closed for new submissions!', 'info')
        return redirect(url_for('admin_challenges'))

    # ------------------------------------------------------------------
    # STUDENT CHALLENGE ROUTES
    # ------------------------------------------------------------------

    @app.route('/challenges')
    @login_required
    def student_challenges():
<<<<<<< HEAD
        challenges = Challenge.query.all()
=======
        challenges = Challenge.query.order_by(Challenge.deadline.desc()).all()
>>>>>>> bfbb0dafae85ae22d2162689d13851f5fdd4774d
        return render_template('student_challenges.html', title='Weekly Challenges', challenges=challenges)

    @app.route('/challenges/<int:challenge_id>', methods=['GET', 'POST'])
    @login_required
    def challenge_detail(challenge_id):
        challenge = Challenge.query.get_or_404(challenge_id)
<<<<<<< HEAD
        existing_submission = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge_id
        ).first()

        if (request.method == 'POST' and not challenge.is_closed and not existing_submission):
            result = request.form.get('result')
            proof = request.files.get('proof_file')
            if proof and result:
                file_fn = save_upload(proof)
=======
        
        existing_submission = Submission.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first()
        submissions = Submission.query.filter_by(challenge_id=challenge.id).order_by(Submission.submitted_at.desc()).all()

        if request.method == 'POST':
            if challenge.is_closed:
                flash('This challenge is closed to new submissions.', 'danger')
                return redirect(url_for('challenge_detail', challenge_id=challenge.id))

            if existing_submission:
                flash('You have already submitted your attempt for this challenge!', 'warning')
                return redirect(url_for('challenge_detail', challenge_id=challenge.id))

            result_text = request.form.get('result')
            proof_file = request.files.get('proof_file')

            if result_text and proof_file and proof_file.filename != '':
                random_hex = secrets.token_hex(8)
                _, f_ext = os.path.splitext(proof_file.filename)
                file_fn = random_hex + f_ext
                
                uploads_dir = os.path.join(app.root_path, 'static/uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                
                file_path = os.path.join(uploads_dir, file_fn)
                proof_file.save(file_path)

>>>>>>> bfbb0dafae85ae22d2162689d13851f5fdd4774d
                new_submission = Submission(
                    user_id=current_user.id,
                    challenge_id=challenge_id,
                    result=result,
                    proof_file=file_fn
                )
                db.session.add(new_submission)
                db.session.commit()
                flash('Your attempt has been submitted! Good luck!', 'success')
                return redirect(url_for('challenge_detail', challenge_id=challenge_id))
            else:
                flash('Please fill in your result and upload a proof image.', 'danger')

        submissions = Submission.query.filter_by(challenge_id=challenge_id).all()
        return render_template('challenge_detail.html', challenge=challenge,
                               existing_submission=existing_submission, submissions=submissions)

    # ------------------------------------------------------------------
    # LEADERBOARD ROUTE
    # ------------------------------------------------------------------

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

        return render_template('leaderboard.html', points_users=points_users, streak_users=streak_users,
                               faculties=faculties, sports=sports,
                               selected_faculty=selected_faculty, selected_sport=selected_sport,
                               title="Leaderboard")

    @app.route("/admin/reset_season", methods=['POST'])
    @login_required
    @admin_required
    def reset_season():
        students = User.query.filter_by(is_admin=False).all()
        for student in students:
            student.points = 0
            student.streak = 0
        db.session.commit()
        flash('The season has been reset. All student rankings are now at zero.', 'warning')
        return redirect(url_for('admin_dashboard'))

    # ------------------------------------------------------------------
    # FEEDBACK ROUTES
    # ------------------------------------------------------------------

    @app.route('/feedback', methods=['GET', 'POST'])
    @login_required
    def submit_feedback():
        form = FeedbackForm()
        if form.validate_on_submit():
            new_feedback = Feedback(
                user_id=current_user.id,
                submission_type=form.submission_type.data,
                message=form.message.data
            )
            db.session.add(new_feedback)
            db.session.commit()
            flash('Thank you! Your feedback has been submitted.', 'success')
            return redirect(url_for('submit_feedback'))
        return render_template('feedback.html', title='Feedback', form=form)

    @app.route('/admin/feedback')
    @login_required
    @admin_required
    def admin_feedback():
        feedbacks = Feedback.query.order_by(Feedback.submitted_at.desc()).all()
        return render_template('admin_feedback.html', title='Manage Feedback', feedbacks=feedbacks)

    @app.route('/admin/feedback/<int:feedback_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_feedback(feedback_id):
        feedback = Feedback.query.get_or_404(feedback_id)
        db.session.delete(feedback)
        db.session.commit()
        flash('Feedback entry deleted.', 'info')
        return redirect(url_for('admin_feedback'))

    # ------------------------------------------------------------------
    # SPORT BUDDY FINDER ROUTES  (Reduction 3 — day-field loop)
    # ------------------------------------------------------------------

    @app.route('/buddy_finder', methods=['GET', 'POST'])
    @login_required
    def buddy_finder():
        form = BuddyAvailabilityForm()

        day_fields = [
            ('Mon', form.mon_time), ('Tue', form.tue_time), ('Wed', form.wed_time),
            ('Thu', form.thu_time), ('Fri', form.fri_time), ('Sat', form.sat_time),
            ('Sun', form.sun_time)
        ]

        if request.method == 'GET':
            if current_user.availability_days:
                saved = {
                    entry.split(':')[0]: entry.split(':')[1]
                    for entry in current_user.availability_days.split(',')
                    if ':' in entry
                }
                for day, field in day_fields:
                    field.data = saved.get(day, '')

        if form.validate_on_submit():
            avail = [f"{day}:{field.data}" for day, field in day_fields if field.data]
            current_user.availability_days = ','.join(avail) if avail else None
            db.session.commit()
            flash('Your detailed weekly schedule has been saved!', 'success')
            return redirect(url_for('buddy_finder'))

        matches = []
        if current_user.availability_days and current_user.sport_preferences:
            my_avail = current_user.availability_days.split(',')
            my_sport = current_user.sport_preferences.lower()

            candidates = User.query.filter(
                User.id != current_user.id,
                User.is_banned == False,
                User.availability_days.isnot(None),
                User.availability_days != '',
                User.sport_preferences.isnot(None),
                User.sport_preferences != ''
            ).all()

            for candidate in candidates:
                if my_sport not in candidate.sport_preferences.lower():
                    continue
                their_avail = candidate.availability_days.split(',')
                shared = list(set(my_avail).intersection(set(their_avail)))
                if not shared:
                    continue
                existing = BuddyRequest.query.filter(
                    ((BuddyRequest.sender_id == current_user.id) & (BuddyRequest.receiver_id == candidate.id)) |
                    ((BuddyRequest.sender_id == candidate.id) & (BuddyRequest.receiver_id == current_user.id))
                ).first()
                matches.append({
                    'user': candidate,
                    'shared_slots': shared,
                    'existing_request': existing
                })

        pending_requests = BuddyRequest.query.filter_by(receiver_id=current_user.id, status='Pending').all()
        confirmed = BuddyRequest.query.filter(
            ((BuddyRequest.sender_id == current_user.id) | (BuddyRequest.receiver_id == current_user.id)),
            BuddyRequest.status == 'Accepted'
        ).all()

        return render_template('buddy_finder.html', title='Sport Buddy Finder', form=form,
                               matches=matches, pending_requests=pending_requests, confirmed=confirmed)

    @app.route('/buddy/request/<int:receiver_id>', methods=['POST'])
    @login_required
    def send_buddy_request(receiver_id):
        receiver = User.query.get_or_404(receiver_id)
        existing = BuddyRequest.query.filter(
            ((BuddyRequest.sender_id == current_user.id) & (BuddyRequest.receiver_id == receiver_id)) |
            ((BuddyRequest.sender_id == receiver_id) & (BuddyRequest.receiver_id == current_user.id))
        ).first()
        if existing:
            flash('A request already exists with this student.', 'info')
        else:
            new_request = BuddyRequest(sender_id=current_user.id, receiver_id=receiver_id, status='Pending')
            db.session.add(new_request)
            db.session.commit()
            flash(f'Meetup request sent to {receiver.name}!', 'success')
        return redirect(url_for('buddy_finder'))

    @app.route('/buddy/respond/<int:request_id>/<string:action>', methods=['POST'])
    @login_required
    def respond_buddy_request(request_id, action):
        buddy_req = BuddyRequest.query.get_or_404(request_id)
        if buddy_req.receiver_id != current_user.id:
            abort(403)
        if action == 'accept':
            buddy_req.status = 'Accepted'
            db.session.commit()
            flash(f'You are now matched with {buddy_req.sender.name}!', 'success')
        elif action == 'decline':
            buddy_req.status = 'Declined'
            db.session.commit()
            flash('Request declined.', 'info')
        return redirect(url_for('buddy_finder'))

    # ------------------------------------------------------------------
    # ADMIN TASK REVIEWS
    # ------------------------------------------------------------------

    @app.route('/admin/task_reviews')
    @login_required
    @admin_required
    def admin_task_reviews():
        pending_tasks = UserTask.query.filter_by(status='Pending Review').all()
        return render_template('admin_task_reviews.html', pending_tasks=pending_tasks, title="Daily Quest Reviews")

    @app.route('/admin/task_reviews/<int:utask_id>/<action>', methods=['POST'])
    @login_required
    @admin_required
    def verify_daily_task(utask_id, action):
        utask = UserTask.query.get_or_404(utask_id)

        if action == 'approve':
            utask.status = 'Completed'
            utask.user_ref.points += 10
            pt = Point(user_id=utask.user_id, amount=10, source=f"Admin Verified: {utask.task_ref.title}")
            db.session.add(pt)
            db.session.commit()
            bonus = check_daily_completion(utask.user_ref)
            if bonus:
                flash(f"Proof approved! This completed their daily 3. They were awarded a +{bonus} point bonus!", 'success')
            else:
                flash(f"Proof approved for {utask.user_ref.name}'s task. +10 Points allocated!", 'success')

        elif action == 'reject':
            utask.status = 'In Progress'
            flash(f"Proof rejected. {utask.user_ref.name} has been notified to resubmit.", 'warning')

        db.session.commit()
        return redirect(url_for('admin_task_reviews'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)