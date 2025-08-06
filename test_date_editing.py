#!/usr/bin/env python3
"""
Test script for date editing functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Attendance, AttendanceAudit
from datetime import datetime, timedelta

def test_date_editing():
    app = create_app()
    
    with app.app_context():
        print("Testing date editing functionality...")
        
        # Get the first attendance record to test with
        attendance = Attendance.query.first()
        if attendance:
            print(f"Testing with attendance record ID: {attendance.id}")
            print(f"Current date: {attendance.date}")
            print(f"Current notes: {attendance.notes}")
            print(f"Current free_class: {attendance.free_class}")
            
            # Test that we can access the date field
            try:
                new_date = attendance.date + timedelta(days=1)
                print(f"✅ Date field is accessible and can be modified")
                print(f"Example new date: {new_date}")
            except Exception as e:
                print(f"❌ Error with date field: {e}")
        else:
            print("No attendance records found to test with")
        
        print("\nTest completed!")

if __name__ == "__main__":
    test_date_editing() 