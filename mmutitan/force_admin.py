from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    # Look for your specific email
    user = User.query.filter_by(email='admin555@gmail.com').first()
    
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"SUCCESS: {user.name} (admin555@gmail.com) is now an Admin.")
    else:
        print("ERROR: User not found. Did you register with 'admin555@gmail.com' yet?")