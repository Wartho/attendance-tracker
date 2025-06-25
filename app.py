from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import qrcode
from io import BytesIO
import base64
from flask.cli import with_appcontext
import click

# Get the directory where app.py is located
basedir = os.path.abspath(os.path.dirname(__file__))
# Set template folder to app/templates
template_dir = os.path.join(basedir, 'app', 'templates')
# Set database path to instance/app.db
db_path = os.path.join(basedir, 'instance', 'app.db')

app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime)
    uq_user_qr_code_id = db.Column(db.String(36))
    profile_picture = db.Column(db.String(255))
    belt_level = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    program = db.Column(db.String(20))
    plan = db.Column(db.String(20))
    classes = db.Column(db.String(10))
    phone_number = db.Column(db.String(20))
    effective_from = db.Column(db.Date)
    effective_to = db.Column(db.Date)
    gender = db.Column(db.String(10))
    qr_code_id = db.Column(db.Text)
    
    def is_teacher(self):
        return self.role == 'teacher'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@click.command('clear-users')
@with_appcontext
def clear_users():
    """Clear all users from the database."""
    User.query.delete()
    db.session.commit()
    click.echo('All users have been cleared from the database.')

app.cli.add_command(clear_users)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your username and password.')
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', f'{username}@example.com')  # Default email
        first_name = request.form.get('first_name', username)  # Default to username
        last_name = request.form.get('last_name', '')  # Default empty
        role = request.form.get('role', 'student')  # Default to student
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.')
        else:
            new_user = User(
                username=username, 
                password_hash=generate_password_hash(password),
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/qrcode')
@login_required
def qrcode():
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(current_user.username)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return render_template('qrcode.html', img_data=img_data)

if __name__ == '__main__':
    app.run(debug=True) 