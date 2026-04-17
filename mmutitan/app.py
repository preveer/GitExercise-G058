from flask import Flask, render_template, url_for, flash, redirect
from flask_login import login_user, current_user, logout_user, login_required
from config import Config
from models import db, login_manager, User, Badge 
from forms import RegistrationForm, LoginForm # Added LoginForm here

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
            return redirect(url_for('login')) # Redirect to login after registering
        return render_template('register.html', title='Register', form=form)

    # --- ADDED LOGIN ROUTE ---
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

    # --- ADDED LOGOUT ROUTE ---
    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('home'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)