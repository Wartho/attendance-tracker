from app import db, create_app
from app.models import User

app = create_app()

with app.app_context():
    # Drop the existing users table
    db.drop_all()

    # Recreate the users table without the unique constraint on email
    db.create_all()

    print("Users table recreated without the unique constraint on email.") 