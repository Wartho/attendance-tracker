from app import db, create_app
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='dadjoke').first()
    if user:
        print('User "dadjoke" exists in the database.')
    else:
        print('User "dadjoke" does NOT exist in the database.') 