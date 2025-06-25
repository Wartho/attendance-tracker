from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, time, timedelta
import qrcode
from io import BytesIO
import base64
from flask.cli import with_appcontext
import click
import pytz
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
from PIL import Image
from werkzeug.utils import secure_filename
from collections import OrderedDict
import calendar
from datetime import date
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
migrate = Migrate(app, db)
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

def get_pacific_datetime():
    """Get current datetime in Pacific timezone (naive)"""
    return get_pacific_now().replace(tzinfo=None)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=get_pacific_datetime)
    qr_code_id = db.Column(db.String(36), unique=True, name='uq_user_qr_code_id', default=lambda: str(uuid.uuid4()))
    profile_picture = db.Column(db.String(255))  # Store the filename of the profile picture
    belt_level = db.Column(db.String(20), default='Not Set')  # No Belt, Not Set, White, Yellow, Green, Purple, Purple-Blue, Blue, Blue-Brown, Brown, Brown-Red, Red, Red-Black, Black
    
    # New personal information fields
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # Male, Female, Other
    program = db.Column(db.String(20), nullable=True)  # 3 months, 6 months, 1 year
    plan = db.Column(db.String(20), nullable=True)  # 1/week, 2/week
    effective_from = db.Column(db.Date, nullable=True)  # Effective period start date
    effective_to = db.Column(db.Date, nullable=True)  # Effective period end date
    classes = db.Column(db.String(10), nullable=True)  # 48, 96
    phone_number = db.Column(db.String(20), nullable=True)
    
    # Student's attendance records
    student_attendances = db.relationship('Attendance', 
                                       foreign_keys='Attendance.student_id',
                                       backref='student', 
                                       lazy='dynamic')
    
    # Teacher's marked attendance records
    teacher_attendances = db.relationship('Attendance',
                                       foreign_keys='Attendance.created_by',
                                       backref='teacher',
                                       lazy='dynamic')
    
    # Belt history records
    belt_history = db.relationship('BeltHistory',
                                 backref='student',
                                 lazy='dynamic',
                                 order_by='BeltHistory.date_obtained.desc()')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_teacher(self):
        return self.role == 'teacher'

    def generate_qr_code_data(self):
        return f"student:{self.qr_code_id}"

class BeltHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    belt_level = db.Column(db.String(20), nullable=False)
    date_obtained = db.Column(db.Date, nullable=False, default=get_pacific_date)
    created_at = db.Column(db.DateTime, default=get_pacific_datetime)
    updated_at = db.Column(db.DateTime, default=get_pacific_datetime, onupdate=get_pacific_datetime)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'present', 'absent', 'late'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_pacific_datetime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=get_pacific_datetime, onupdate=get_pacific_datetime)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=True)  # Link to specific class
    check_in_time = db.Column(db.Time, nullable=True)  # Actual check-in time within class window
    check_in_method = db.Column(db.String(20), nullable=True)  # 'qr_code' or 'manual'

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Monday Morning Adults"
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    min_belt_level = db.Column(db.String(50), nullable=True)  # e.g., "White" or None for all levels
    max_belt_level = db.Column(db.String(50), nullable=True)  # e.g., "Green" or None for all levels
    max_capacity = db.Column(db.Integer, nullable=True)  # NULL for unlimited
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_pacific_datetime)
    updated_at = db.Column(db.DateTime, default=get_pacific_datetime, onupdate=get_pacific_datetime)
    
    # Relationships
    enrollments = db.relationship('ClassEnrollment', backref='class_info', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='class_info', lazy='dynamic')
    
    def get_day_name(self):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[self.day_of_week]
    
    def get_time_range(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
    
    def get_belt_range_display(self):
        if self.min_belt_level and self.max_belt_level:
            return f"{self.min_belt_level} - {self.max_belt_level}"
        elif self.min_belt_level:
            return f"{self.min_belt_level} and up"
        elif self.max_belt_level:
            return f"Up to {self.max_belt_level}"
        else:
            return "All levels"

class ClassEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    enrolled_from = db.Column(db.Date, nullable=False, default=get_pacific_date)
    enrolled_until = db.Column(db.Date, nullable=True)  # NULL for ongoing enrollment
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_pacific_datetime)
    updated_at = db.Column(db.DateTime, default=get_pacific_datetime, onupdate=get_pacific_datetime)
    
    # Relationship
    student = db.relationship('User', backref='class_enrollments')

class ClassHoliday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200), nullable=True)  # e.g., "Christmas", "Spring Break"
    is_recurring = db.Column(db.Boolean, default=False)  # True for annual holidays like Christmas
    created_at = db.Column(db.DateTime, default=get_pacific_datetime)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@click.command('clear-users')
@with_appcontext
def clear_users():
    """Clear all users from the database."""
    User.query.delete()
    db.session.commit()
    click.echo('All users have been cleared from the database.')

app.cli.add_command(clear_users)

@app.route('/')
@login_required
def index():
    if current_user.is_teacher():
        return redirect(url_for('teacher_home'))
    return redirect(url_for('student_home'))

@app.route('/teacher/home')
@login_required
def teacher_home():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Get students with their last attended information
    students_with_last_attended = db.session.query(
        User,
        db.func.max(Attendance.created_at).label('last_attended')
    ).outerjoin(
        Attendance, User.id == Attendance.student_id
    ).filter(
        User.role == 'student'
    ).group_by(
        User.id
    ).order_by(
        db.func.max(Attendance.created_at).desc().nullslast()
    ).all()
    
    # Extract students and their last attended info
    students = []
    for student, last_attended in students_with_last_attended:
        if last_attended:
            # Convert UTC datetime to Pacific timezone
            pacific_time = last_attended.replace(tzinfo=pytz.UTC).astimezone(PACIFIC_TZ)
            student.last_attended = pacific_time
        else:
            student.last_attended = last_attended
        students.append(student)
    
    today = get_pacific_date().strftime('%Y-%m-%d')
    return render_template('teacher/dashboard.html', students=students, today=today)

@app.route('/student/home')
@login_required
def student_home():
    if current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    attendances = current_user.student_attendances.all()
    return render_template('student/dashboard.html', attendances=attendances)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your username and password.')
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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
            return redirect(url_for('index'))
    return render_template('auth/register.html')

@app.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Only teachers can mark attendance'}), 403
    
    # Handle both JSON data (QR code) and form data (manual marking)
    if request.is_json:
        data = request.get_json()
        if not data or 'qr_data' not in data:
            return jsonify({'success': False, 'message': 'Invalid QR code data'}), 400
        
        try:
            # Parse the QR code data
            qr_data = data['qr_data']
            if not qr_data.startswith('student:'):
                return jsonify({'success': False, 'message': 'Invalid QR code format'}), 400
                
            qr_code_id = qr_data.split(':')[1]
            
            # Get the student using qr_code_id
            student = User.query.filter_by(qr_code_id=qr_code_id, role='student').first()
            if not student:
                return jsonify({'success': False, 'message': 'Student not found'}), 404
            
            # Check if attendance already marked for today
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
            
            # Create attendance record
            attendance = Attendance(
                student_id=student.id,
                date=today,
                status='present',
                created_by=current_user.id
            )
            db.session.add(attendance)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'student_name': f"{student.first_name} {student.last_name}"
            })
        except Exception as e:
            db.session.rollback()
            print(f"Error marking attendance: {str(e)}")
            return jsonify({'success': False, 'message': 'Error processing attendance'}), 500
    
    else:
        # Handle form data from manual attendance marking
        try:
            # Check if this is individual student attendance
            student_id = request.form.get('student_id')
            if student_id:
                # Individual student attendance
                student = User.query.filter_by(id=student_id, role='student').first()
                if not student:
                    flash('Student not found', 'danger')
                    return redirect(url_for('teacher_home'))
                
                date_str = request.form.get('date')
                status = request.form.get('status')
                notes = request.form.get('notes', '')
                
                if not date_str or not status:
                    flash('Date and status are required', 'danger')
                    return redirect(url_for('teacher_home'))
                
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Create new attendance record (allow duplicates)
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
                return redirect(url_for('teacher_home'))
            
            else:
                # Bulk attendance marking (existing functionality)
                date_str = request.form.get('date')
                if not date_str:
                    flash('Date is required', 'danger')
                    return redirect(url_for('teacher_home'))
                
                attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Process each student's attendance
                for student in User.query.filter_by(role='student').all():
                    status_key = f'status_{student.id}'
                    notes_key = f'notes_{student.id}'
                    
                    if status_key in request.form:
                        status = request.form[status_key]
                        notes = request.form.get(notes_key, '')
                        
                        # Create new attendance record (allow duplicates)
                        attendance = Attendance(
                            student_id=student.id,
                            date=attendance_date,
                            status=status,
                            notes=notes,
                            created_by=current_user.id
                        )
                        db.session.add(attendance)
                
                db.session.commit()
                flash('Attendance marked for all students!', 'success')
                return redirect(url_for('teacher_home'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error marking attendance: {str(e)}', 'danger')
            return redirect(url_for('teacher_home'))

@app.route('/scan_qr', methods=['GET', 'POST'])
@login_required
def scan_qr():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        qr_data = request.form.get('qr_data')
        if qr_data:
            # Process QR code data
            response = mark_attendance()
            if response.status_code == 200:
                flash('Attendance marked successfully!', 'success')
            else:
                flash('Error marking attendance.', 'danger')
            return redirect(url_for('scan_qr'))
    
    return render_template('main/scan_qr.html')

@app.route('/student/qr_code')
@login_required
def student_qr_code():
    if current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(current_user.generate_qr_code_data())
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return render_template('student/qr_code.html', img_data=img_data)

@app.route('/teacher/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
        else:
            new_student = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='student'
            )
            new_student.set_password(password)
            db.session.add(new_student)
            db.session.commit()
            flash('Student added successfully!')
            return redirect(url_for('teacher_home'))
    
    return render_template('teacher/add_student.html')

@app.route('/teacher/print_student_qr/<int:student_id>')
@login_required
def print_student_qr(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('teacher_home'))
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(student.generate_qr_code_data())
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add student info
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 100, f"Student QR Code")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 120, f"Name: {student.first_name} {student.last_name}")
    p.drawString(50, height - 140, f"Username: {student.username}")
    
    # Convert QR code to image and add to PDF
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    # Add QR code image to PDF
    p.drawImage(img_io, 50, height - 400, width=200, height=200)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'qr_code_{student.username}.pdf')

@app.route('/student/<int:student_id>/calendar')
@login_required
def student_calendar(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('teacher_home'))
    
    # Get current month and year
    now = datetime.now()
    month = request.args.get('month', now.month, type=int)
    year = request.args.get('year', now.year, type=int)
    
    # Create calendar
    cal = calendar.monthcalendar(year, month)
    
    # Get attendance data for the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    attendances = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()
    
    # Create attendance lookup
    attendance_lookup = {att.date: att.status for att in attendances}
    
    return render_template('teacher/student_calendar.html', 
                         student=student, 
                         calendar=cal, 
                         month=month, 
                         year=year,
                         attendance_lookup=attendance_lookup)

@app.route('/student/<int:student_id>/upload_picture', methods=['POST'])
@login_required
def upload_profile_picture(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('teacher_home'))
    
    if 'profile_picture' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('teacher_home'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('teacher_home'))
    
    if file:
        # Secure the filename
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{student_id}_{timestamp}_{filename}"
        
        # Save file
        file_path = os.path.join('app/static/profile_pictures', filename)
        file.save(file_path)
        
        # Update student record
        student.profile_picture = filename
        db.session.commit()
        
        flash('Profile picture uploaded successfully!', 'success')
    
    return redirect(url_for('teacher_home'))

@app.route('/student/<int:student_id>/update_belt_level', methods=['POST'])
@login_required
def update_belt_level(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('teacher_home'))
    
    belt_level = request.form.get('belt_level')
    if belt_level:
        student.belt_level = belt_level
        db.session.commit()
        flash('Belt level updated successfully!', 'success')
    
    return redirect(url_for('teacher_home'))

@app.route('/student/<int:student_id>/belt_history', methods=['GET'])
@login_required
def get_belt_history(student_id):
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    history = BeltHistory.query.filter_by(student_id=student_id).order_by(BeltHistory.date_obtained.desc()).all()
    
    return jsonify([{
        'id': h.id,
        'belt_level': h.belt_level,
        'date_obtained': h.date_obtained.strftime('%Y-%m-%d'),
        'created_at': h.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for h in history])

@app.route('/student/<int:student_id>/belt_history/<int:history_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_belt_history(student_id, history_id):
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    history = BeltHistory.query.filter_by(id=history_id, student_id=student_id).first()
    if not history:
        return jsonify({'error': 'History record not found'}), 404
    
    if request.method == 'DELETE':
        db.session.delete(history)
        db.session.commit()
        return jsonify({'message': 'History record deleted'})
    
    # PUT request to update
    data = request.get_json()
    if data.get('belt_level'):
        history.belt_level = data['belt_level']
    if data.get('date_obtained'):
        history.date_obtained = datetime.strptime(data['date_obtained'], '%Y-%m-%d').date()
    
    db.session.commit()
    return jsonify({'message': 'History record updated'})

@app.route('/student/<int:student_id>/add_belt_history', methods=['POST'])
@login_required
def add_belt_history(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('teacher_home'))
    
    belt_level = request.form.get('belt_level')
    date_obtained = request.form.get('date_obtained')
    
    if belt_level and date_obtained:
        try:
            date_obj = datetime.strptime(date_obtained, '%Y-%m-%d').date()
            history = BeltHistory(
                student_id=student_id,
                belt_level=belt_level,
                date_obtained=date_obj
            )
            db.session.add(history)
            db.session.commit()
            flash('Belt history added successfully!', 'success')
        except ValueError:
            flash('Invalid date format.', 'danger')
    else:
        flash('Belt level and date are required.', 'danger')
    
    return redirect(url_for('teacher_home'))

@app.route('/student/<int:student_id>/update_personal_info', methods=['POST'])
@login_required
def update_personal_info(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('teacher_home'))
    
    # Update personal information fields
    student.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
    student.gender = request.form.get('gender')
    student.program = request.form.get('program')
    student.plan = request.form.get('plan')
    student.effective_from = datetime.strptime(request.form.get('effective_from'), '%Y-%m-%d').date() if request.form.get('effective_from') else None
    student.effective_to = datetime.strptime(request.form.get('effective_to'), '%Y-%m-%d').date() if request.form.get('effective_to') else None
    student.classes = request.form.get('classes')
    student.phone_number = request.form.get('phone_number')
    
    db.session.commit()
    flash('Personal information updated successfully!', 'success')
    
    return redirect(url_for('teacher_home'))

@app.route('/classes')
@login_required
def class_management():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    classes = Class.query.all()
    return render_template('teacher/classes.html', classes=classes)

@app.route('/add_class', methods=['POST'])
@login_required
def add_class():
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        name = request.form.get('name')
        day_of_week = int(request.form.get('day_of_week'))
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        min_belt_level = request.form.get('min_belt_level')
        max_belt_level = request.form.get('max_belt_level')
        max_capacity = int(request.form.get('max_capacity')) if request.form.get('max_capacity') else None
        
        new_class = Class(
            name=name,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            min_belt_level=min_belt_level,
            max_belt_level=max_belt_level,
            max_capacity=max_capacity
        )
        
        db.session.add(new_class)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Class added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/edit_class/<int:class_id>', methods=['POST'])
@login_required
def edit_class(class_id):
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({'error': 'Class not found'}), 404
    
    try:
        class_obj.name = request.form.get('name')
        class_obj.day_of_week = int(request.form.get('day_of_week'))
        class_obj.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        class_obj.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        class_obj.min_belt_level = request.form.get('min_belt_level')
        class_obj.max_belt_level = request.form.get('max_belt_level')
        class_obj.max_capacity = int(request.form.get('max_capacity')) if request.form.get('max_capacity') else None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Class updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/class/<int:class_id>/data')
@login_required
def get_class_data(class_id):
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({'error': 'Class not found'}), 404
    
    return jsonify({
        'id': class_obj.id,
        'name': class_obj.name,
        'day_of_week': class_obj.day_of_week,
        'start_time': class_obj.start_time.strftime('%H:%M'),
        'end_time': class_obj.end_time.strftime('%H:%M'),
        'min_belt_level': class_obj.min_belt_level,
        'max_belt_level': class_obj.max_belt_level,
        'max_capacity': class_obj.max_capacity
    })

@app.route('/check_existing_attendance')
@login_required
def check_existing_attendance():
    if not current_user.is_teacher():
        return jsonify({'error': 'Access denied'}), 403
    
    student_id = request.args.get('student_id', type=int)
    date_str = request.args.get('date')
    
    if not student_id or not date_str:
        return jsonify({'error': 'Missing student_id or date'}), 400
    
    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing_attendance = Attendance.query.filter_by(
            student_id=student_id,
            date=attendance_date
        ).first()
        
        if existing_attendance:
            return jsonify({
                'exists': True,
                'status': existing_attendance.status,
                'notes': existing_attendance.notes
            })
        else:
            return jsonify({'exists': False})
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 