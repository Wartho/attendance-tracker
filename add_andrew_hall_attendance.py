#!/usr/bin/env python3
"""
Script to add dummy attendance data for Andrew Hall
Adds 29 attendance records across the past 12 months
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Attendance
from datetime import datetime, timedelta
import random
import pytz

def add_andrew_hall_attendance():
    app = create_app()
    
    with app.app_context():
        # Find Andrew Hall
        andrew = User.query.filter_by(first_name='Andrew', last_name='Hall', role='student').first()
        
        if not andrew:
            print("Andrew Hall not found in the database!")
            return
        
        # Find a teacher to mark the attendance
        teacher = User.query.filter_by(role='teacher').first()
        if not teacher:
            print("No teacher found in the database!")
            return
        
        # Generate 29 dates across the past 12 months
        # Focus on weekdays (Monday-Friday) and some weekends
        today = datetime.now()
        dates = []
        
        # Generate dates for the past 12 months
        for i in range(365):
            date = today - timedelta(days=i)
            # 70% chance for weekdays, 30% chance for weekends
            if date.weekday() < 5:  # Monday-Friday
                if random.random() < 0.7:
                    dates.append(date)
            else:  # Saturday-Sunday
                if random.random() < 0.3:
                    dates.append(date)
            
            if len(dates) >= 29:
                break
        
        # Shuffle dates to make them more random
        random.shuffle(dates)
        dates = dates[:29]
        
        # Add attendance records
        attendance_count = 0
        for date in dates:
            # Check if attendance already exists for this date
            existing = Attendance.query.filter_by(
                student_id=andrew.id,
                date=date.date()
            ).first()
            
            if existing:
                print(f"Attendance already exists for {date.date()}, skipping...")
                continue
            
            # Generate random time between 9 AM and 8 PM
            hour = random.randint(9, 20)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            attendance_time = date.replace(hour=hour, minute=minute, second=second)
            
            # Create attendance record
            attendance = Attendance(
                student_id=andrew.id,
                date=date.date(),
                status='present',
                notes='',
                created_by=teacher.id,
                created_at=attendance_time
            )
            
            db.session.add(attendance)
            attendance_count += 1
            print(f"Added attendance for {date.date()} at {attendance_time.strftime('%H:%M:%S')}")
        
        try:
            db.session.commit()
            print(f"\nSuccessfully added {attendance_count} attendance records for Andrew Hall!")
            print(f"Total attendance records for Andrew Hall: {andrew.student_attendances.count()}")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding attendance: {e}")

if __name__ == '__main__':
    add_andrew_hall_attendance() 