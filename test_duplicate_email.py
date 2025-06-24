from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create first user
    user1 = User(
        username='test1',
        email='test@example.com',
        first_name='Test',
        last_name='User1',
        password_hash=generate_password_hash('password'),
        role='student'
    )
    
    # Create second user with same email
    user2 = User(
        username='test2',
        email='test@example.com',
        first_name='Test',
        last_name='User2',
        password_hash=generate_password_hash('password'),
        role='student'
    )
    
    try:
        db.session.add(user1)
        db.session.commit()
        print("First user created successfully")
        
        db.session.add(user2)
        db.session.commit()
        print("Second user created successfully - email is NOT unique")
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback() 