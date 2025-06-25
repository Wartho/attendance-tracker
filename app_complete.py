from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, date, time
import uuid
from sqlalchemy import text
import click
from flask.cli import with_appcontext
import pytz
from io import BytesIO
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
from PIL import Image

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

# Pacific timezone
PACIFIC_TZ = pytz.timezone('US/Pacific')

def get_pacific_now():
    """Get current datetime in Pacific timezone"""
    return datetime.now(PACIFIC_TZ)

def get_pacific_date():
    """Get current date in Pacific timezone"""
    return get_pacific_now().date()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(255))  # Increased length for longer hashes
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=get_pacific_now)
    qr_code_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    profile_picture = db.Column(db.String(255))
    belt_level = db.Column(db.String(20), default='Not Set')
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    program = db.Column(db.String(20))
    plan = db.Column(db.String(20))
    effective_from = db.Column(db.Date)
    effective_to = db.Column(db.Date)
    classes = db.Column(db.String(10))
    phone_number = db.Column(db.String(20))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_teacher(self):
        return self.role == 'teacher'

    def generate_qr_code_data(self):
        return f"student:{self.qr_code_id}"

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'late'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_pacific_now)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=get_pacific_now, onupdate=get_pacific_now)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    check_in_time = db.Column(db.Time)
    check_in_method = db.Column(db.String(20))  # 'qr_code' or 'manual'

class BeltHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    belt_level = db.Column(db.String(20), nullable=False)
    date_obtained = db.Column(db.Date, nullable=False, default=get_pacific_date)
    created_at = db.Column(db.DateTime, default=get_pacific_now)
    updated_at = db.Column(db.DateTime, default=get_pacific_now, onupdate=get_pacific_now)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    min_belt_level = db.Column(db.String(50))
    max_belt_level = db.Column(db.String(50))
    max_capacity = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_pacific_now)
    updated_at = db.Column(db.DateTime, default=get_pacific_now, onupdate=get_pacific_now)

class ClassEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    enrolled_from = db.Column(db.Date, nullable=False, default=get_pacific_date)
    enrolled_until = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_pacific_now)
    updated_at = db.Column(db.DateTime, default=get_pacific_now, onupdate=get_pacific_now)

class ClassHoliday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    is_recurring = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_pacific_now)

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
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 0; }
            .feature-card { background: white; border-radius: 10px; padding: 30px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .feature-icon { font-size: 3rem; color: #667eea; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="hero">
            <div class="container text-center">
                <h1 class="display-4 mb-4">🎉 Attendance Tracker</h1>
                <p class="lead mb-4">Complete martial arts attendance management system</p>
                <div class="d-flex justify-content-center gap-3">
                    <a href="/login" class="btn btn-light btn-lg">Login</a>
                    <a href="/register" class="btn btn-outline-light btn-lg">Register</a>
                </div>
            </div>
        </div>
        
        <div class="container my-5">
            <div class="row">
                <div class="col-md-4">
                    <div class="feature-card text-center">
                        <div class="feature-icon">
                            <i class="fas fa-qrcode"></i>
                        </div>
                        <h4>QR Code Attendance</h4>
                        <p>Quick and easy attendance tracking with QR codes</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="feature-card text-center">
                        <div class="feature-icon">
                            <i class="fas fa-belt"></i>
                        </div>
                        <h4>Belt Management</h4>
                        <p>Track student progress and belt level history</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="feature-card text-center">
                        <div class="feature-icon">
                            <i class="fas fa-users"></i>
                        </div>
                        <h4>Class Management</h4>
                        <p>Organize classes and manage enrollments</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Login failed. Please check your username and password.')
        except Exception as e:
            flash(f'Login error: {str(e)}')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Attendance Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .login-container { max-width: 400px; margin: 100px auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="login-container">
                <div class="card shadow">
                    <div class="card-body p-4">
                        <h2 class="text-center mb-4">Login</h2>
                        {% with messages = get_flashed_messages() %}
                            {% if messages %}
                                {% for message in messages %}
                                    <div class="alert alert-danger">{{ message }}</div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        <form method="POST">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        <div class="text-center mt-3">
                            <a href="/register">Don't have an account? Register here</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
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
        except Exception as e:
            flash(f'Registration error: {str(e)}')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - Attendance Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .register-container { max-width: 500px; margin: 50px auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="register-container">
                <div class="card shadow">
                    <div class="card-body p-4">
                        <h2 class="text-center mb-4">Register</h2>
                        {% with messages = get_flashed_messages() %}
                            {% if messages %}
                                {% for message in messages %}
                                    <div class="alert alert-danger">{{ message }}</div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        <form method="POST">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="username" class="form-label">Username</label>
                                        <input type="text" class="form-control" id="username" name="username" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="email" class="form-label">Email</label>
                                        <input type="email" class="form-control" id="email" name="email" required>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="first_name" class="form-label">First Name</label>
                                        <input type="text" class="form-control" id="first_name" name="first_name" required>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label for="last_name" class="form-label">Last Name</label>
                                        <input type="text" class="form-control" id="last_name" name="last_name" required>
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="role" class="form-label">Role</label>
                                <select class="form-select" id="role" name="role" required>
                                    <option value="teacher">Teacher</option>
                                    <option value="student">Student</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Register</button>
                        </form>
                        <div class="text-center mt-3">
                            <a href="/login">Already have an account? Login here</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        if current_user.is_teacher():
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    except Exception as e:
        return f'Dashboard error: {str(e)}', 500

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if not current_user.is_teacher():
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('index'))
    
    students = User.query.filter_by(role='student').all()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teacher Dashboard - Attendance Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="/dashboard">Attendance Tracker</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/scan_qr"><i class="fas fa-qrcode"></i> Scan QR</a>
                    <a class="nav-link" href="/add_student"><i class="fas fa-user-plus"></i> Add Student</a>
                    <a class="nav-link" href="/classes"><i class="fas fa-users"></i> Classes</a>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h3 class="mb-0">Student Management</h3>
                            <div>
                                <a href="/scan_qr" class="btn btn-primary me-2">
                                    <i class="fas fa-qrcode"></i> Scan QR Codes
                                </a>
                                <a href="/add_student" class="btn btn-success">
                                    <i class="fas fa-user-plus"></i> Add Student
                                </a>
                            </div>
                        </div>
                        <div class="card-body">
                            {% if students %}
                                <div class="table-responsive">
                                    <table class="table table-striped">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Username</th>
                                                <th>Email</th>
                                                <th>Belt Level</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for student in students %}
                                            <tr>
                                                <td>{{ student.first_name }} {{ student.last_name }}</td>
                                                <td>{{ student.username }}</td>
                                                <td>{{ student.email }}</td>
                                                <td>{{ student.belt_level or 'Not Set' }}</td>
                                                <td>
                                                    <div class="btn-group" role="group">
                                                        <a href="/student/{{ student.id }}/profile" class="btn btn-sm btn-outline-primary">
                                                            <i class="fas fa-user"></i> Profile
                                                        </a>
                                                        <a href="/student/{{ student.id }}/qr" class="btn btn-sm btn-outline-info">
                                                            <i class="fas fa-qrcode"></i> QR Code
                                                        </a>
                                                        <button class="btn btn-sm btn-outline-success" onclick="markAttendance({{ student.id }}, '{{ student.first_name }} {{ student.last_name }}')">
                                                            <i class="fas fa-calendar-check"></i> Mark
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                <p class="text-center text-muted">No students found.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Mark Attendance Modal -->
        <div class="modal fade" id="markAttendanceModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Mark Attendance</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <form id="attendanceForm" method="POST" action="/mark_attendance">
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="student_name" class="form-label">Student</label>
                                <input type="text" class="form-control" id="student_name" readonly>
                                <input type="hidden" id="student_id" name="student_id">
                            </div>
                            <div class="mb-3">
                                <label for="date" class="form-label">Date</label>
                                <input type="date" class="form-control" id="date" name="date" required value="{{ today }}">
                            </div>
                            <div class="mb-3">
                                <label for="status" class="form-label">Status</label>
                                <select class="form-select" id="status" name="status" required>
                                    <option value="present">Present</option>
                                    <option value="absent">Absent</option>
                                    <option value="late">Late</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label for="notes" class="form-label">Notes</label>
                                <textarea class="form-control" id="notes" name="notes" rows="3"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Mark Attendance</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function markAttendance(studentId, studentName) {
                document.getElementById('student_id').value = studentId;
                document.getElementById('student_name').value = studentName;
                new bootstrap.Modal(document.getElementById('markAttendanceModal')).show();
            }
        </script>
    </body>
    </html>
    ''', students=students, today=date.today().isoformat())

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_teacher():
        flash('Access denied. Students only.', 'danger')
        return redirect(url_for('index'))
    
    attendances = Attendance.query.filter_by(student_id=current_user.id).order_by(Attendance.date.desc()).limit(10).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Student Dashboard - Attendance Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="/dashboard">Attendance Tracker</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/student/qr_code"><i class="fas fa-qrcode"></i> My QR Code</a>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h3 class="mb-0">Welcome, {{ current_user.first_name }}!</h3>
                            <a href="/student/qr_code" class="btn btn-primary">
                                <i class="fas fa-qrcode"></i> Download QR Code
                            </a>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Your Information</h5>
                                    <p><strong>Name:</strong> {{ current_user.first_name }} {{ current_user.last_name }}</p>
                                    <p><strong>Belt Level:</strong> {{ current_user.belt_level or 'Not Set' }}</p>
                                    <p><strong>Program:</strong> {{ current_user.program or 'Not Set' }}</p>
                                </div>
                                <div class="col-md-6">
                                    <h5>Recent Attendance</h5>
                                    {% if attendances %}
                                        <div class="table-responsive">
                                            <table class="table table-sm">
                                                <thead>
                                                    <tr>
                                                        <th>Date</th>
                                                        <th>Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {% for attendance in attendances %}
                                                    <tr>
                                                        <td>{{ attendance.date.strftime('%Y-%m-%d') }}</td>
                                                        <td>
                                                            <span class="badge {% if attendance.status == 'present' %}bg-success{% elif attendance.status == 'late' %}bg-warning{% else %}bg-danger{% endif %}">
                                                                {{ attendance.status }}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                    {% endfor %}
                                                </tbody>
                                            </table>
                                        </div>
                                    {% else %}
                                        <p class="text-muted">No attendance records found.</p>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', attendances=attendances)

@app.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    if not current_user.is_teacher():
        flash('Only teachers can mark attendance.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    try:
        student_id = request.form.get('student_id')
        date_str = request.form.get('date')
        status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        if not all([student_id, date_str, status]):
            flash('Missing required fields.', 'danger')
            return redirect(url_for('teacher_dashboard'))
        
        student = User.query.filter_by(id=student_id, role='student').first()
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('teacher_dashboard'))
        
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        attendance = Attendance(
            student_id=student.id,
            date=attendance_date,
            status=status,
            notes=notes,
            created_by=current_user.id
        )
        db.session.add(attendance)
        db.session.commit()
        
        flash(f'Attendance marked for {student.first_name} {student.last_name}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error marking attendance: {str(e)}', 'danger')
    
    return redirect(url_for('teacher_dashboard'))

@app.route('/scan_qr')
@login_required
def scan_qr():
    if not current_user.is_teacher():
        flash('Only teachers can scan QR codes.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scan QR Code - Attendance Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            #reader { width: 100%; max-width: 600px; margin: 0 auto; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="/dashboard">Attendance Tracker</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/teacher/dashboard"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="mb-0">Scan Student QR Code</h3>
                        </div>
                        <div class="card-body text-center">
                            <div id="reader"></div>
                            <div id="result" class="alert mt-3" style="display: none;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://unpkg.com/html5-qrcode"></script>
        <script>
            let html5QrCode = new Html5Qrcode("reader");
            
            function onScanSuccess(decodedText, decodedResult) {
                // Stop scanning
                html5QrCode.stop().then(() => {
                    // Process the QR code
                    fetch('/mark_attendance_qr', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            qr_data: decodedText
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const result = document.getElementById('result');
                        result.style.display = 'block';
                        
                        if (data.success) {
                            result.className = 'alert alert-success';
                            result.innerHTML = `✅ Attendance marked for ${data.student_name}`;
                        } else {
                            result.className = 'alert alert-danger';
                            result.innerHTML = `❌ ${data.message}`;
                        }
                        
                        // Restart scanning after 3 seconds
                        setTimeout(() => {
                            result.style.display = 'none';
                            startScanning();
                        }, 3000);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        const result = document.getElementById('result');
                        result.style.display = 'block';
                        result.className = 'alert alert-danger';
                        result.innerHTML = '❌ Error processing attendance';
                        
                        setTimeout(() => {
                            result.style.display = 'none';
                            startScanning();
                        }, 3000);
                    });
                });
            }
            
            function onScanFailure(error) {
                // Handle scan failure, usually ignore
                console.warn(`QR code scanning failed: ${error}`);
            }
            
            function startScanning() {
                html5QrCode.start(
                    { facingMode: "environment" },
                    {
                        fps: 10,
                        qrbox: { width: 250, height: 250 }
                    },
                    onScanSuccess,
                    onScanFailure
                );
            }
            
            // Start scanning when page loads
            startScanning();
        </script>
    </body>
    </html>
    ''')

@app.route('/mark_attendance_qr', methods=['POST'])
@login_required
def mark_attendance_qr():
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Only teachers can mark attendance'}), 403
    
    try:
        data = request.get_json()
        if not data or 'qr_data' not in data:
            return jsonify({'success': False, 'message': 'Invalid QR code data'}), 400
        
        qr_data = data['qr_data']
        if not qr_data.startswith('student:'):
            return jsonify({'success': False, 'message': 'Invalid QR code format'}), 400
            
        qr_code_id = qr_data.split(':')[1]
        
        student = User.query.filter_by(qr_code_id=qr_code_id, role='student').first()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        
        today = get_pacific_date()
        existing_attendance = Attendance.query.filter_by(
            student_id=student.id,
            date=today
        ).first()
        
        if existing_attendance:
            return jsonify({
                'success': False,
                'message': f'Attendance already marked for {student.first_name} {student.last_name} today'
            }), 400
        
        attendance = Attendance(
            student_id=student.id,
            date=today,
            status='present',
            created_by=current_user.id,
            check_in_method='qr_code'
        )
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'student_name': f"{student.first_name} {student.last_name}"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error processing attendance'}), 500

@app.route('/student/qr_code')
@login_required
def student_qr_code():
    if current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(current_user.generate_qr_code_data())
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Attendance QR Code for {current_user.username}")
    p.drawString(100, 730, "Print this page and bring it to class for attendance.")
    
    # Save QR code to buffer
    img_buffer = BytesIO()
    qr_img.save(img_buffer)
    img_buffer.seek(0)
    
    # Add QR code to PDF
    p.drawImage(img_buffer, 100, 400, width=400, height=400)
    p.save()
    
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"attendance_qr_{current_user.username}.pdf",
        mimetype='application/pdf'
    )

@app.route('/add_student')
@login_required
def add_student():
    if not current_user.is_teacher():
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Add Student - Attendance Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="/dashboard">Attendance Tracker</a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/teacher/dashboard"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
                    <a class="nav-link" href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="mb-0">Add New Student</h3>
                        </div>
                        <div class="card-body">
                            <form method="POST" action="/add_student">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="username" class="form-label">Username</label>
                                            <input type="text" class="form-control" id="username" name="username" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="email" class="form-label">Email</label>
                                            <input type="email" class="form-control" id="email" name="email" required>
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="first_name" class="form-label">First Name</label>
                                            <input type="text" class="form-control" id="first_name" name="first_name" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="last_name" class="form-label">Last Name</label>
                                            <input type="text" class="form-control" id="last_name" name="last_name" required>
                                        </div>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <div class="mb-3">
                                    <label for="belt_level" class="form-label">Belt Level</label>
                                    <select class="form-select" id="belt_level" name="belt_level">
                                        <option value="Not Set">Not Set</option>
                                        <option value="White">White</option>
                                        <option value="Yellow">Yellow</option>
                                        <option value="Green">Green</option>
                                        <option value="Purple">Purple</option>
                                        <option value="Blue">Blue</option>
                                        <option value="Brown">Brown</option>
                                        <option value="Red">Red</option>
                                        <option value="Black">Black</option>
                                    </select>
                                </div>
                                <button type="submit" class="btn btn-primary">Add Student</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''')

@app.route('/add_student', methods=['POST'])
@login_required
def add_student_post():
    if not current_user.is_teacher():
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        username = request.form['username']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        belt_level = request.form.get('belt_level', 'Not Set')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('add_student'))
        
        new_student = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='student',
            belt_level=belt_level
        )
        new_student.set_password(password)
        db.session.add(new_student)
        db.session.commit()
        
        flash(f'Student {first_name} {last_name} added successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding student: {str(e)}', 'danger')
        return redirect(url_for('add_student'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'message': 'Attendance Tracker is running!', 'database': 'connected'}
    except Exception as e:
        return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}, 500

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Create all database tables."""
    db.create_all()
    print("Database tables created successfully!")

app.cli.add_command(init_db_command)

if __name__ == '__main__':
    app.run(debug=True) 