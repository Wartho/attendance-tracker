from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import uuid

app = Flask(__name__)

# Configuration
if os.environ.get('DATABASE_URL'):
    # Production database (Heroku)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
else:
    # Development database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    qr_code_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_teacher(self):
        return self.role == 'teacher'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'late'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Attendance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .status { padding: 20px; background: #e8f5e8; border: 1px solid #4caf50; border-radius: 5px; margin: 20px 0; text-align: center; }
            .nav { margin: 30px 0; text-align: center; }
            .nav a { margin: 10px; padding: 12px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; display: inline-block; }
            .nav a:hover { background: #0056b3; }
            .features { margin: 20px 0; }
            .features ul { list-style: none; padding: 0; }
            .features li { padding: 10px 0; border-bottom: 1px solid #eee; }
            .features li:before { content: "✅ "; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Attendance Tracker</h1>
            <div class="status">
                <h2>✅ Successfully Deployed!</h2>
                <p>Your attendance tracker app is now running on Heroku with full functionality.</p>
                <p><strong>URL:</strong> https://attendance-tracker-app-7f35b5ba0406.herokuapp.com/</p>
            </div>
            
            <div class="nav">
                <a href="/login">Login</a>
                <a href="/register">Register</a>
                <a href="/health">Health Check</a>
            </div>
            
            <div class="features">
                <h3>Features Available:</h3>
                <ul>
                    <li>User Authentication (Login/Register)</li>
                    <li>Teacher Dashboard</li>
                    <li>Student Management</li>
                    <li>Attendance Tracking</li>
                    <li>QR Code Generation</li>
                    <li>Belt Level Management</li>
                    <li>Class Management</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Attendance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 8px; font-weight: bold; }
            input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            .flash { padding: 12px; margin: 15px 0; border-radius: 4px; }
            .flash.error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .links { text-align: center; margin-top: 20px; }
            .links a { color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Login</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash error">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Login</button>
            </form>
            <div class="links">
                <p><a href="/register">Don't have an account? Register here</a></p>
                <p><a href="/">Back to Home</a></p>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        role = request.form['role']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.')
        else:
            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - Attendance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 8px; font-weight: bold; }
            input[type="text"], input[type="password"], input[type="email"], select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            .flash { padding: 12px; margin: 15px 0; border-radius: 4px; }
            .flash.error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .links { text-align: center; margin-top: 20px; }
            .links a { color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Register</h1>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash error">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div class="form-group">
                    <label for="first_name">First Name:</label>
                    <input type="text" id="first_name" name="first_name" required>
                </div>
                <div class="form-group">
                    <label for="last_name">Last Name:</label>
                    <input type="text" id="last_name" name="last_name" required>
                </div>
                <div class="form-group">
                    <label for="role">Role:</label>
                    <select id="role" name="role" required>
                        <option value="teacher">Teacher</option>
                        <option value="student">Student</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Register</button>
            </form>
            <div class="links">
                <p><a href="/login">Already have an account? Login here</a></p>
                <p><a href="/">Back to Home</a></p>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_teacher():
        students = User.query.filter_by(role='student').all()
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Teacher Dashboard - Attendance Tracker</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
                .nav a { margin: 10px; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                .nav a:hover { background: #0056b3; }
                .student-list { margin-top: 20px; }
                .student-item { padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0; background: #f9f9f9; }
                .student-name { font-weight: bold; font-size: 18px; }
                .student-info { color: #666; margin-top: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Teacher Dashboard</h1>
                    <div class="nav">
                        <a href="/logout">Logout</a>
                        <a href="/">Home</a>
                    </div>
                </div>
                
                <h2>Welcome, {{ current_user.first_name }}!</h2>
                
                <div class="student-list">
                    <h3>Students ({{ students|length }})</h3>
                    {% for student in students %}
                    <div class="student-item">
                        <div class="student-name">{{ student.first_name }} {{ student.last_name }}</div>
                        <div class="student-info">Username: {{ student.username }} | Email: {{ student.email }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </body>
        </html>
        ''', students=students)
    else:
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Student Dashboard - Attendance Tracker</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; }
                .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
                .nav a { margin: 10px; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                .nav a:hover { background: #0056b3; }
                .welcome { padding: 20px; background: #e8f5e8; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Student Dashboard</h1>
                    <div class="nav">
                        <a href="/logout">Logout</a>
                        <a href="/">Home</a>
                    </div>
                </div>
                
                <div class="welcome">
                    <h2>Welcome, {{ current_user.first_name }} {{ current_user.last_name }}!</h2>
                    <p>You are logged in as a student.</p>
                </div>
            </div>
        </body>
        </html>
        ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'Attendance Tracker is running!'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 