from app import create_app, db
from models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='admin555@gmail.com').first()
    if user:
        user.is_admin = True
        db.session.commit()
        print("\n" + "="*40)
        print(f"SUCCESS: {user.name} is now an ADMIN!")
        print("="*40 + "\n")
    else:
        print("\n" + "!"*40)
        print("ERROR: User 'admin555@gmail.com' not found.")
        print("Please register on the website first!")
        print("!"*40 + "\n")