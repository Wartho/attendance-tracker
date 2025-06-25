from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import uuid
import pytz

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

# We'll define the models here but import db later to avoid circular imports
def init_models(db, login_manager):
    global User, BeltHistory, Attendance, Class, ClassEnrollment, ClassHoliday
    
    class User(UserMixin, db.Model):
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

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

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
    
    return User, BeltHistory, Attendance, Class, ClassEnrollment, ClassHoliday 