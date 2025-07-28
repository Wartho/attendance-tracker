from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Attendance, BeltHistory, Class
from app.forms import RegistrationForm, AddStudentForm, ClassForm
from datetime import datetime, time, timedelta
import pytz
from io import BytesIO
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile
import os
from PIL import Image
from werkzeug.utils import secure_filename
from collections import OrderedDict
import calendar
from datetime import date
import logging

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

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

@main.route('/')
@main.route('/index')
@login_required
def index():
    if current_user.is_teacher():
        return redirect(url_for('main.teacher_home'))
    return redirect(url_for('main.student_home'))

@main.route('/teacher/home')
@login_required
def teacher_home():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
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

@main.route('/student/home')
@login_required
def student_home():
    if current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    attendances = current_user.student_attendances.all()
    return render_template('student/dashboard.html', attendances=attendances)

@main.route('/mark_attendance', methods=['POST'])
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
                    return redirect(url_for('main.teacher_home'))
                
                date_str = request.form.get('date')
                status = request.form.get('status')
                notes = request.form.get('notes', '')
                
                if not date_str or not status:
                    flash('Date and status are required', 'danger')
                    return redirect(url_for('main.teacher_home'))
                
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
                return redirect(url_for('main.teacher_home'))
            
            else:
                # Bulk attendance marking (existing functionality)
                date_str = request.form.get('date')
                if not date_str:
                    flash('Date is required', 'danger')
                    return redirect(url_for('main.teacher_home'))
                
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
                flash('Attendance marked successfully!', 'success')
                return redirect(url_for('main.teacher_home'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error marking attendance: {str(e)}")
            flash('Error marking attendance', 'danger')
            return redirect(url_for('main.teacher_home'))

@main.route('/scan_qr', methods=['GET', 'POST'])
@login_required
def scan_qr():
    if not current_user.is_teacher():
        flash('Only teachers can scan QR codes.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        qr_data = request.form.get('qr_data')
        if not qr_data or not qr_data.startswith('student:'):
            flash('Invalid QR code.', 'danger')
            return redirect(url_for('main.scan_qr'))
        
        student_id = qr_data.split(':')[1]
        student = User.query.filter_by(qr_code_id=student_id, role='student').first()
        
        if not student:
            flash('Student not found.', 'danger')
            return redirect(url_for('main.scan_qr'))
        
        # Check if within valid time window (9 AM to 9 PM Pacific)
        pacific = pytz.timezone('US/Pacific')
        current_time = datetime.now(pacific).time()
        if not (time(9, 0) <= current_time <= time(21, 0)):
            flash('Attendance can only be marked between 9 AM and 9 PM Pacific time.', 'danger')
            return redirect(url_for('main.scan_qr'))
        
        # Create new attendance record (allow duplicates)
        today = datetime.now(pacific).date()
        attendance = Attendance(
            student_id=student.id,
            date=today,
            status='present',
            created_by=current_user.id
        )
        db.session.add(attendance)
        db.session.commit()
        
        flash(f'Attendance marked for {student.username}.', 'success')
        return redirect(url_for('main.scan_qr'))
    
    return render_template('main/scan_qr.html')

@main.route('/student/qr_code')
@login_required
def student_qr_code():
    if current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
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

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid username or password', 'danger')
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    from flask import Response
    if not current_user.is_authenticated:
        return Response("If you need to register a new user, please log in first", mimetype="text/plain")
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("register")
    logger.debug(f"Form data: {request.form}")
    form = RegistrationForm()
    if form.validate_on_submit():
        logger.debug("Form validated successfully.")
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data if form.gender.data else None,
            program=form.program.data if form.program.data else None,
            plan=form.plan.data if form.plan.data else None,
            classes=form.classes.data if form.classes.data else None,
            phone_number=form.phone_number.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            logger.debug("User registered and committed to DB.")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {e}")
            flash('Error during registration. Username or email might already exist.', 'danger')
    else:
        if request.method == 'POST':
            logger.debug(f"Form validation failed. Errors: {form.errors}")
    return render_template('auth/register.html', form=form)

@main.route('/teacher/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    form = AddStudentForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='student',
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data if form.gender.data else None,
            program=form.program.data if form.program.data else None,
            plan=form.plan.data if form.plan.data else None,
            classes=form.classes.data if form.classes.data else None,
            phone_number=form.phone_number.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('main.teacher_home'))
        except Exception as e:
            db.session.rollback()
            flash('Error: Username or email may already exist.', 'danger')
    return render_template('teacher/add_student.html', form=form)

@main.route('/teacher/print_student_qr/<int:student_id>')
@login_required
def print_student_qr(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main.teacher_home'))
    
    try:
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(student.generate_qr_code_data())
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Create PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add text
        p.drawString(100, 750, f"Attendance QR Code for {student.username}")
        p.drawString(100, 730, f"Name: {student.first_name} {student.last_name}")
        p.drawString(100, 710, "Print this page and bring it to class for attendance.")
        
        # Save QR code to a temporary file
        import tempfile
        import os
        import time
        from PIL import Image
        
        # Create a temporary file with a unique name
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f'qr_{student.id}_{int(time.time())}.png')
        
        try:
            # Convert QR image to PIL Image if it's not already
            if not isinstance(qr_img, Image.Image):
                qr_img = qr_img.convert('RGB')
            qr_img.save(temp_file)
            
            # Add QR code to PDF with reduced size (125x125)
            p.drawImage(temp_file, 100, 400, width=125, height=125)
            
            # Add student's name underneath the QR code
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, 380, f"{student.first_name} {student.last_name}")
            
            p.save()
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass  # Ignore cleanup errors
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"attendance_qr_{student.username}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")  # For debugging
        flash('Error generating QR code. Please try again.', 'danger')
        return redirect(url_for('main.teacher_home')) 

@main.route('/student/<int:student_id>/calendar')
@login_required
def student_calendar(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main.teacher_home'))
    
    # Get all attendance records for the student
    attendances = Attendance.query.filter_by(student_id=student.id).all()
    
    # --- Attendance Stats for last 12 months ---
    today = get_pacific_date()
    stats = OrderedDict()
    for i in range(11, -1, -1):
        month = (today.month - i - 1) % 12 + 1
        year = today.year if today.month - i > 0 else today.year - 1
        label = f"{calendar.month_abbr[month]} {str(year)[2:]}"
        stats[label] = 0
    for att in attendances:
        if att.status == 'present' and att.date:
            label = f"{calendar.month_abbr[att.date.month]} {str(att.date.year)[2:]}"
            if label in stats:
                stats[label] += 1
    attendance_stats = stats
    # ---
    
    # Format attendance data for FullCalendar
    attendance_events = []
    for attendance in attendances:
        teacher = User.query.get(attendance.created_by)
        teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else "Unknown"
        color = {
            'present': '#28a745',
            'absent': '#dc3545',
            'late': '#ffc107'
        }.get(attendance.status, '#6c757d')
        event = {
            'title': attendance.status.capitalize(),
            'start': attendance.date.strftime('%Y-%m-%d'),
            'allDay': True,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#ffffff',
            'notes': attendance.notes,
            'marked_by': teacher_name
        }
        attendance_events.append(event)
    return render_template('teacher/student_calendar.html', 
                         student=student, 
                         attendance_events=attendance_events,
                         today=get_pacific_date().strftime('%Y-%m-%d'),
                         Attendance=Attendance,
                         attendance_stats=attendance_stats)

@main.route('/student/<int:student_id>/upload_picture', methods=['POST'])
@login_required
def upload_profile_picture(student_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('main.teacher_home'))
    
    if 'profile_picture' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('main.student_calendar', student_id=student_id))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('main.student_calendar', student_id=student_id))
    
    if file:
        # Create profile_pictures directory if it doesn't exist
        upload_folder = os.path.join(current_app.static_folder, 'profile_pictures')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Secure the filename and add student ID to make it unique
        filename = secure_filename(file.filename)
        filename = f"{student_id}_{filename}"
        
        # Save the file
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Process the image
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate target dimensions while maintaining aspect ratio
                target_width = 150
                target_height = 200
                target_ratio = target_width / target_height
                
                # Get current dimensions
                width, height = img.size
                current_ratio = width / height
                
                if current_ratio > target_ratio:
                    # Image is wider than target ratio
                    new_width = int(height * target_ratio)
                    left = (width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, height))
                else:
                    # Image is taller than target ratio
                    new_height = int(width / target_ratio)
                    top = (height - new_height) // 2
                    img = img.crop((0, top, width, top + new_height))
                
                # Resize to target dimensions
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                img.save(filepath)
                
                # Update student's profile picture in database
                student.profile_picture = filename
                db.session.commit()
                
                flash('Profile picture uploaded successfully.', 'success')
        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'danger')
            return redirect(url_for('main.student_calendar', student_id=student_id))
    
    return redirect(url_for('main.student_calendar', student_id=student_id)) 

@main.route('/student/<int:student_id>/update_belt_level', methods=['POST'])
@login_required
def update_belt_level(student_id):
    import logging
    logger = logging.getLogger("belt_level_update")
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Only teachers can update belt levels'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    data = request.get_json()
    if not data or 'belt_level' not in data:
        return jsonify({'success': False, 'message': 'Belt level is required'}), 400
    
    try:
        old_belt_level = student.belt_level
        new_belt_level = data['belt_level']
        
        # Only create history entry if belt level actually changed and is not "Not Set"
        if old_belt_level != new_belt_level and new_belt_level not in ['Not Set', 'No Belt']:
            belt_history = BeltHistory(
                student_id=student.id,
                belt_level=new_belt_level,
                date_obtained=datetime.utcnow().date()
            )
            db.session.add(belt_history)
        
        student.belt_level = new_belt_level
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating belt level: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Error updating belt level'}), 500

@main.route('/student/<int:student_id>/belt_history', methods=['GET'])
@login_required
def get_belt_history(student_id):
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Only teachers can view belt history'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    try:
        belt_history = BeltHistory.query.filter_by(student_id=student.id).order_by(BeltHistory.date_obtained.desc()).all()
        
        history_data = []
        for entry in belt_history:
            history_data.append({
                'id': entry.id,
                'belt_level': entry.belt_level,
                'date_obtained': entry.date_obtained.strftime('%Y-%m-%d')
            })
        
        return jsonify({'success': True, 'belt_history': history_data})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error retrieving belt history'}), 500

@main.route('/student/<int:student_id>/belt_history/<int:history_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_belt_history(student_id, history_id):
    import logging
    logger = logging.getLogger("belt_history")
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Only teachers can manage belt history'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    try:
        belt_entry = BeltHistory.query.filter_by(id=history_id, student_id=student.id).first()
        if not belt_entry:
            return jsonify({'success': False, 'message': 'Belt history entry not found'}), 404
        
        if request.method == 'DELETE':
            db.session.delete(belt_entry)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Belt history entry deleted'})
        
        elif request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
            
            if 'belt_level' in data:
                belt_entry.belt_level = data['belt_level']
            if 'date_obtained' in data:
                belt_entry.date_obtained = datetime.strptime(data['date_obtained'], '%Y-%m-%d').date()
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Belt history entry updated'})
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing belt history: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Error managing belt history'}), 500

@main.route('/student/<int:student_id>/add_belt_history', methods=['POST'])
@login_required
def add_belt_history(student_id):
    import logging
    logger = logging.getLogger("add_belt_history")
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Only teachers can add belt history'}), 403
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    data = request.get_json()
    logger.debug(f"Received data: {data}")
    if not data or 'belt_level' not in data or 'date_obtained' not in data:
        logger.error("Missing belt_level or date_obtained in data")
        return jsonify({'success': False, 'message': 'Belt level and date obtained are required'}), 400
    try:
        belt_entry = BeltHistory(
            student_id=student.id,
            belt_level=data['belt_level'],
            date_obtained=datetime.strptime(data['date_obtained'], '%Y-%m-%d').date()
        )
        db.session.add(belt_entry)
        db.session.commit()
        logger.info("Belt history entry added successfully")
        return jsonify({'success': True, 'message': 'Belt history entry added'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding belt history entry: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Error adding belt history entry'}), 500

@main.route('/student/<int:student_id>/update_personal_info', methods=['POST'])
@login_required
def update_personal_info(student_id):
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Only teachers can update personal information'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    try:
        # Update allowed fields (excluding username)
        if 'first_name' in data:
            student.first_name = data['first_name']
        if 'last_name' in data:
            student.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != student.id:
                return jsonify({'success': False, 'message': 'Email is already taken by another user'}), 400
            student.email = data['email']
        if 'date_of_birth' in data:
            if data['date_of_birth']:
                student.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            else:
                student.date_of_birth = None
        if 'gender' in data:
            student.gender = data['gender']
        if 'phone_number' in data:
            student.phone_number = data['phone_number']
        if 'belt_level' in data:
            old_belt_level = student.belt_level
            new_belt_level = data['belt_level']
            if old_belt_level != new_belt_level and new_belt_level and new_belt_level != 'No Belt':
                from app.models import BeltHistory
                belt_history = BeltHistory(
                    student_id=student.id,
                    belt_level=new_belt_level,
                    date_obtained=datetime.utcnow().date()
                )
                db.session.add(belt_history)
            student.belt_level = new_belt_level
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating personal information: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating personal information'}), 500

@main.route('/classes')
@login_required
def class_management():
    if not current_user.is_teacher():
        abort(403)
    from app.forms import ClassForm
    form = ClassForm()
    classes = Class.query.order_by(Class.day_of_week, Class.start_time).all()
    return render_template('teacher/classes.html', classes=classes, form=form)

@main.route('/add_class', methods=['POST'])
@login_required
def add_class():
    if not current_user.is_teacher():
        abort(403)
    from app.forms import ClassForm
    form = ClassForm()
    if form.validate_on_submit():
        new_class = Class(
            name=form.name.data,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            min_belt_level=form.min_belt_level.data or None,
            max_belt_level=form.max_belt_level.data or None,
            max_capacity=form.max_capacity.data,
            is_active=form.is_active.data
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Class added successfully!', 'success')
    else:
        flash('Error adding class. Please check the form.', 'danger')
    return redirect(url_for('main.class_management'))

@main.route('/edit_class/<int:class_id>', methods=['POST'])
@login_required
def edit_class(class_id):
    if not current_user.is_teacher():
        abort(403)
    from app.forms import ClassForm
    form = ClassForm()
    c = Class.query.get_or_404(class_id)
    if form.validate_on_submit():
        c.name = form.name.data
        c.day_of_week = form.day_of_week.data
        c.start_time = form.start_time.data
        c.end_time = form.end_time.data
        c.min_belt_level = form.min_belt_level.data or None
        c.max_belt_level = form.max_belt_level.data or None
        c.max_capacity = form.max_capacity.data
        c.is_active = form.is_active.data
        db.session.commit()
        flash('Class updated successfully!', 'success')
    else:
        flash('Error updating class. Please check the form.', 'danger')
    return redirect(url_for('main.class_management')) 

@main.route('/class/<int:class_id>/data')
@login_required
def get_class_data(class_id):
    if not current_user.is_teacher():
        abort(403)
    c = Class.query.get_or_404(class_id)
    return jsonify({
        'id': c.id,
        'name': c.name,
        'day_of_week': c.day_of_week,
        'start_time': c.start_time.strftime('%H:%M'),
        'end_time': c.end_time.strftime('%H:%M'),
        'min_belt_level': c.min_belt_level or '',
        'max_belt_level': c.max_belt_level or '',
        'max_capacity': c.max_capacity,
        'is_active': c.is_active
    }) 

@main.route('/check_existing_attendance')
@login_required
def check_existing_attendance():
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    student_id = request.args.get('student_id')
    date_str = request.args.get('date')
    
    if not student_id or not date_str:
        return jsonify({'success': False, 'message': 'Student ID and date are required'}), 400
    
    try:
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        existing_attendance = Attendance.query.filter_by(
            student_id=student_id,
            date=attendance_date
        ).first()
        
        return jsonify({
            'success': True,
            'exists': existing_attendance is not None
        })
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error checking attendance'}), 500

# Plan routes
@main.route('/student/<int:student_id>/plan', methods=['GET'])
@login_required
def get_plan(student_id):
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    # Return the student's current plan data
    plans = []
    if student.program or student.plan or student.classes or student.effective_from:
        plans.append({
            'id': 1,  # Placeholder ID
            'program': student.program,
            'effective_date': student.effective_from.strftime('%Y-%m-%d') if student.effective_from else None,
            'plan': student.plan,
            'classes': student.classes
        })
    
    # Sort by effective_date in descending order (most recent first)
    plans.sort(key=lambda x: x['effective_date'] if x['effective_date'] else '', reverse=True)
    
    return jsonify({'success': True, 'plans': plans})

@main.route('/student/<int:student_id>/plan/<int:plan_id>/remaining', methods=['GET'])
def get_plan_remaining(student_id, plan_id):
    """Calculate remaining classes for a specific plan"""
    student = User.query.get_or_404(student_id)
    
    # Get the plan data (currently stored in User model)
    if not student.program or not student.effective_from:
        return jsonify({'success': False, 'remaining': 0, 'message': 'No plan data found'})
    
    # Calculate effective end date based on program
    effective_to = None
    if student.program == "3 months":
        effective_to = student.effective_from + timedelta(days=90)
    elif student.program == "6 months":
        effective_to = student.effective_from + timedelta(days=180)
    elif student.program == "1 year":
        effective_to = student.effective_from + timedelta(days=365)
    
    if not effective_to:
        return jsonify({'success': False, 'remaining': 0, 'message': 'Invalid program duration'})
    
    # Set time range (12:01am to 11:59pm)
    start_datetime = datetime.combine(student.effective_from, time(0, 1))  # 12:01am
    end_datetime = datetime.combine(effective_to, time(23, 59))  # 11:59pm
    
    # Count attended classes in the date range
    from app.models import Attendance
    attended_count = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.created_at >= start_datetime,
        Attendance.created_at <= end_datetime
    ).count()
    
    # Calculate remaining classes
    total_classes = int(student.classes) if student.classes and student.classes.isdigit() else 0
    remaining = max(0, total_classes - attended_count)
    
    return jsonify({
        'success': True, 
        'remaining': remaining,
        'attended': attended_count,
        'total': total_classes,
        'effective_from': student.effective_from.strftime('%Y-%m-%d'),
        'effective_to': effective_to.strftime('%Y-%m-%d')
    })

@main.route('/student/<int:student_id>/plan', methods=['POST'])
@login_required
def add_plan(student_id):
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update the student's plan information
        if 'program' in data:
            student.program = data['program']
        if 'effective_date' in data:
            from datetime import datetime
            student.effective_from = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
        if 'plan' in data:
            student.plan = data['plan']
        if 'classes' in data:
            student.classes = data['classes']
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Plan updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating plan'}), 500

@main.route('/student/<int:student_id>/plan/<int:plan_id>', methods=['PUT', 'DELETE'])
@login_required
def manage_plan(student_id, plan_id):
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    if request.method == 'DELETE':
        try:
            # For now, clear the student's plan information
            # In the future, this could delete from a separate Plan model
            student.program = None
            student.plan = None
            student.classes = None
            student.effective_from = None
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Plan deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error deleting plan'}), 500
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        try:
            # Update the student's plan information
            if 'program' in data:
                student.program = data['program']
            if 'effective_date' in data:
                from datetime import datetime
                student.effective_from = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
            if 'plan' in data:
                student.plan = data['plan']
            if 'classes' in data:
                student.classes = data['classes']
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Plan updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error updating plan'}), 500

@main.route('/student/<int:student_id>/attendance_history')
@login_required
def get_attendance_history(student_id):
    if not current_user.is_teacher():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    try:
        # Get attendance history ordered by date descending
        attendance_history = []
        for attendance in student.student_attendances.order_by(Attendance.created_at.desc()).all():
            attendance_history.append({
                'id': attendance.id,
                'created_at': attendance.created_at.strftime('%Y-%m-%d %H:%M') + ' PT',
                'notes': attendance.notes,
                'teacher_name': f"{attendance.teacher.first_name} {attendance.teacher.last_name}" if attendance.teacher else 'Unknown'
            })
        
        return jsonify({'success': True, 'attendance_history': attendance_history})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error loading attendance history'}), 500 