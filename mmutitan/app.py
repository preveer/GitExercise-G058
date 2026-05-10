import os
import secrets
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
# Added Challenge and Submission here!
from models import Task, db, login_manager, User, Badge, Event, RSVP, UserTask, Challenge, Submission
# Added ChallengeForm here!
from forms import RegistrationForm, LoginForm, EventForm, ChangePasswordForm, UpdateProfileForm, TaskForm, ChallengeForm 
from config import Config
import random
import datetime
from datetime import date   

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
        new_rsvp = RSVP(user_id=current_user.id, event_id=event.id, waitlisted=(count >= event.max_capacity))
        db.session.add(new_rsvp)
        db.session.commit()
        flash('RSVP Successful!', 'success')
        return redirect(url_for('list_events'))
        
    @app.route('/cancel_rsvp/<int:event_id>', methods=['POST'])
    @login_required
    def cancel_rsvp(event_id):
        rsvp = RSVP.query.filter_by(user_id=current_user.id, event_id=event_id).first()
        if not rsvp:
            flash('You are not RSVP\'d.', 'danger')
            return redirect(url_for('list_events'))
        was_confirmed = not rsvp.waitlisted
        db.session.delete(rsvp)
        if was_confirmed:
            next_in_line = RSVP.query.filter_by(event_id=event_id, waitlisted=True).order_by(RSVP.id).first()
            if next_in_line:
                next_in_line.waitlisted = False 
        db.session.commit()
        flash('RSVP successfully cancelled.', 'success')
        return redirect(url_for('list_events'))

    # NEW: Check-in logic to award points and badge
    @app.route('/checkin/<int:event_id>', methods=['POST'])
    @login_required
    def checkin(event_id):
        rsvp = RSVP.query.filter_by(user_id=current_user.id, event_id=event_id).first()
        if rsvp and not rsvp.waitlisted and not rsvp.checked_in:
            rsvp.checked_in = True
            current_user.points += 50 # Bonus points!
            
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

    # --- TASK ROUTES ---

    @app.route('/admin/tasks/add', methods=['GET', 'POST'])
    @login_required
    def add_task():
        if not current_user.is_admin:
            return redirect(url_for('home'))
        form = TaskForm()
        if form.validate_on_submit():
            new_task = Task(title=form.title.data, description=form.description.data,
                           sport_category=form.sport_category.data, difficulty=form.difficulty.data,
                           proof_required=form.proof_required.data)
            db.session.add(new_task)
            db.session.commit()
            flash('New task added!', 'success')
            return redirect(url_for('admin_tasks'))
        return render_template('admin_task_form.html', form=form, legend='Add New Task')

    @app.route('/admin/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
    @login_required
    def edit_task(task_id):
        task = Task.query.get_or_404(task_id)
        form = TaskForm()
        if form.validate_on_submit():
            task.title, task.description = form.title.data, form.description.data
            db.session.commit()
            return redirect(url_for('admin_tasks'))
        elif request.method == 'GET':
            form.title.data, form.description.data = task.title, task.description
        return render_template('admin_task_form.html', form=form, legend='Edit Task')

    @app.route('/admin/tasks/delete/<int:task_id>', methods=['POST'])
    @login_required
    def delete_task(task_id):
        # Security: Ensure only admins can perform this action
        if not current_user.is_admin:
            return redirect(url_for('home'))

        task = Task.query.get_or_404(task_id)

        # STEP 1: Delete all UserTask records linked to this task id
        # This prevents the 'NOT NULL constraint failed' error
        UserTask.query.filter_by(task_id=task.id).delete()

        # STEP 2: Now delete the master Task itself
        db.session.delete(task)
        db.session.commit()

        # Note: Ensure 'admin_tasks' is the correct name of your task list route
        return redirect(url_for('admin_tasks'))
    
    @app.route('/daily_tasks')
    @login_required
    def daily_tasks():
        today = date.today()

        # 1. Check if the user already has tasks assigned for TODAY
        today_tasks = UserTask.query.filter(
            UserTask.user_id == current_user.id,
            db.func.date(UserTask.date_accepted) == today
        ).all()

        # 2. If they have NO tasks for today, generate 3 random ones!
        if len(today_tasks) == 0:
            # Try to match their sport preference first
            if current_user.sport_preferences:
                pool = Task.query.filter(Task.sport_category.ilike(f"%{current_user.sport_preferences}%")).all()
            else:
                pool = Task.query.all()

            # If the specific pool is too small, just use all available tasks
            if len(pool) < 3:
                pool = Task.query.all()

            # Pick up to 3 random tasks
            if len(pool) > 0:
                chosen_tasks = random.sample(pool, min(3, len(pool)))
                
                # Assign them to the user
                for t in chosen_tasks:
                    new_ut = UserTask(user_id=current_user.id, task_id=t.id, status='In Progress')
                    db.session.add(new_ut)
                db.session.commit()

                # Refresh the list to show them on the page
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
                # Re-using your exact same profile photo saver!
                picture_file = save_picture(file) 
                user_task.proof_image = picture_file
        user_task.status = 'Pending Review' if user_task.task.proof_required else 'Completed'
        db.session.commit()

        # --- Check if they finished all 3 tasks today ---
        today = date.today()
        all_today = UserTask.query.filter(
            UserTask.user_id == current_user.id,
            db.func.date(UserTask.date_accepted) == today
        ).all()

        # If every task today is done or waiting for review, give them points!
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
            flash('🎉 All daily tasks finished! +50 Points and your streak continues!', 'success')
        else:
            flash('Task submitted! Keep going to finish your daily 3.', 'info')

        return redirect(url_for('daily_tasks'))
    @app.route('/leaderboard')
    @login_required
    def admin_challenges():
        if not current_user.is_admin:
            flash('Access denied.', 'danger')
            return redirect(url_for('home'))
        challenges = Challenge.query.all()
        return render_template('admin_challenges.html', title='Manage Challenges', challenges=challenges)

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
                deadline=form.deadline.data,
                scoring_criteria=form.scoring_criteria.data
            )
            db.session.add(new_challenge)
            db.session.commit()
            flash('New weekly challenge created!', 'success')
            return redirect(url_for('admin_challenges'))
        return render_template('admin_challenge_form.html', title='Add Challenge', form=form, legend='Create New Challenge')

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
            challenge.deadline = form.deadline.data
            challenge.scoring_criteria = form.scoring_criteria.data
            db.session.commit()
            flash('Challenge updated!', 'success')
            return redirect(url_for('admin_challenges'))
        elif request.method == 'GET':
            form.title.data = challenge.title
            form.description.data = challenge.description
            form.sport_category.data = challenge.sport_category
            form.deadline.data = challenge.deadline
            form.scoring_criteria.data = challenge.scoring_criteria
        return render_template('admin_challenge_form.html', title='Edit Challenge', form=form, legend='Edit Challenge')

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
        return render_template('admin_submissions.html', title='View Submissions', challenge=challenge, submissions=submissions)

    @app.route('/admin/submissions/<int:submission_id>/verify', methods=['POST'])
    @login_required
    def verify_submission(submission_id):
        if not current_user.is_admin:
            return redirect(url_for('home'))
        submission = Submission.query.get_or_404(submission_id)
        submission.verified = True
        db.session.commit()
        flash('Submission verified successfully!', 'success')
        return redirect(url_for('view_submissions', challenge_id=submission.challenge_id))

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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)