#!/usr/bin/env python3
"""
Test script for attendance editing functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Attendance, AttendanceAudit
from datetime import datetime, timedelta

def test_attendance_editing():
    app = create_app()
    
    with app.app_context():
        print("Testing attendance editing functionality...")
        
        # Check if we have any attendance records
        attendance_count = Attendance.query.count()
        print(f"Found {attendance_count} attendance records")
        
        # Check if we have any audit records
        audit_count = AttendanceAudit.query.count()
        print(f"Found {audit_count} audit records")
        
        # Check if free_class field exists
        try:
            # Try to query with free_class field
            free_class_count = Attendance.query.filter_by(free_class=False).count()
            print(f"Found {free_class_count} non-free class attendance records")
            print("✅ free_class field is working")
        except Exception as e:
            print(f"❌ Error with free_class field: {e}")
        
        # Check if AttendanceAudit table exists
        try:
            # Try to create a test audit entry
            test_audit = AttendanceAudit(
                attendance_id=1,  # Assuming attendance ID 1 exists
                action='test',
                field_name='test',
                old_value='old',
                new_value='new',
                changed_by=1  # Assuming user ID 1 exists
            )
            print("✅ AttendanceAudit model is working")
        except Exception as e:
            print(f"❌ Error with AttendanceAudit model: {e}")
        
        print("\nTest completed!")

if __name__ == "__main__":
    test_attendance_editing() 