#!/usr/bin/env python3
"""
Script to populate Last Attended field for all students by creating attendance records
with random dates between 6 months ago and present.
"""

from app import create_app, db
from app.models import User, Attendance
from datetime import datetime, timedelta
import random

def populate_last_attended():
    app = create_app()
    
    with app.app_context():
        # Get all students
        students = User.query.filter_by(role='student').all()
        
        if not students:
            print("No students found in the database.")
            return
        
        # Get a teacher to use as the creator of attendance records
        teacher = User.query.filter_by(role='teacher').first()
        if not teacher:
            print("No teacher found. Creating a default teacher...")
            teacher = User(
                username='default_teacher',
                email='teacher@example.com',
                first_name='Default',
                last_name='Teacher',
                role='teacher'
            )
            teacher.set_password('password123')
            db.session.add(teacher)
            db.session.commit()
        
        # Calculate date range (6 months ago to now)
        now = datetime.utcnow()
        six_months_ago = now - timedelta(days=180)
        
        print(f"Populating last attended dates for {len(students)} students...")
        print(f"Date range: {six_months_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
        
        # Create attendance records for each student
        for i, student in enumerate(students, 1):
            # Generate random date between 6 months ago and now
            days_between = (now - six_months_ago).days
            random_days = random.randint(0, days_between)
            random_date = six_months_ago + timedelta(days=random_days)
            
            # Generate random time within the day
            random_hour = random.randint(8, 20)  # Between 8 AM and 8 PM
            random_minute = random.randint(0, 59)
            random_second = random.randint(0, 59)
            
            attendance_datetime = random_date.replace(
                hour=random_hour,
                minute=random_minute,
                second=random_second,
                microsecond=0
            )
            
            # Random attendance status (mostly present, some late, few absent)
            status_weights = {'present': 0.7, 'late': 0.2, 'absent': 0.1}
            status = random.choices(list(status_weights.keys()), weights=list(status_weights.values()))[0]
            
            # Create attendance record
            attendance = Attendance(
                student_id=student.id,
                date=attendance_datetime.date(),
                status=status,
                notes=f"Auto-generated attendance record for testing",
                created_by=teacher.id,
                created_at=attendance_datetime
            )
            
            db.session.add(attendance)
            
            print(f"  {i}. {student.first_name} {student.last_name}: {attendance_datetime.strftime('%Y-%m-%d %H:%M')} ({status})")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\nSuccessfully created attendance records for {len(students)} students!")
        
        # Show summary of last attended dates
        print("\nLast attended dates summary:")
        students_with_attendance = db.session.query(
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
        
        for student, last_attended in students_with_attendance:
            if last_attended:
                print(f"  {student.first_name} {student.last_name}: {last_attended.strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"  {student.first_name} {student.last_name}: Never attended")

if __name__ == '__main__':
    populate_last_attended() 