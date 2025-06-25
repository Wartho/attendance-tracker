from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    if os.environ.get('DATABASE_URL'):
        # Production database (Heroku)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    else:
        # Development database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Initialize models after db is set up
    from app.models import init_models
    User, BeltHistory, Attendance, Class, ClassEnrollment, ClassHoliday = init_models(db, login_manager)
    
    # Import and register blueprints
    from app.routes import main, auth
    app.register_blueprint(main)
    app.register_blueprint(auth)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app 