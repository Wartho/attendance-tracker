#!/usr/bin/env python3
"""
Script to check for and fix duplicate "Free Class" text in attendance notes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Attendance

def check_and_fix_free_class_duplicates():
    app = create_app()
    
    with app.app_context():
        print("Checking for duplicate 'Free Class' text in attendance notes...")
        
        # Find attendance records with free_class=True that have "Free Class:" in notes
        attendances = Attendance.query.filter(
            Attendance.free_class == True,
            Attendance.notes.like('%Free Class:%')
        ).all()
        
        print(f"Found {len(attendances)} attendance records with duplicate 'Free Class' text")
        
        for attendance in attendances:
            print(f"Record ID {attendance.id}: {attendance.notes}")
            
            # Remove the "Free Class:" prefix from notes
            if attendance.notes and attendance.notes.startswith('Free Class: '):
                old_notes = attendance.notes
                attendance.notes = attendance.notes.replace('Free Class: ', '', 1)
                print(f"  Fixed: '{old_notes}' -> '{attendance.notes}'")
        
        if attendances:
            db.session.commit()
            print("✅ Fixed all duplicate 'Free Class' text")
        else:
            print("✅ No duplicate 'Free Class' text found")
        
        print("\nCheck completed!")

if __name__ == "__main__":
    check_and_fix_free_class_duplicates() 