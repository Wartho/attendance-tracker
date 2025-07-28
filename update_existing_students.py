#!/usr/bin/env python3
"""
Script to update existing students in production database to use correct dropdown values
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
import random

def update_existing_students():
    app = create_app()
    
    with app.app_context():
        # Get all existing students
        students = User.query.filter_by(role='student').all()
        print(f"Found {len(students)} existing students to update")
        
        # Correct dropdown values
        programs = ["3 months", "6 months", "1 year"]
        plans = ["1/week", "2/week"]
        classes_list = ["48", "96"]
        
        updated_count = 0
        
        for student in students:
            # Update program if it's not a valid dropdown value
            if student.program and student.program not in programs:
                student.program = random.choice(programs)
                print(f"Updated {student.username} program from '{student.program}' to '{student.program}'")
            
            # Update plan if it's not a valid dropdown value
            if student.plan and student.plan not in plans:
                student.plan = random.choice(plans)
                print(f"Updated {student.username} plan from '{student.plan}' to '{student.plan}'")
            
            # Update classes if it's not a valid dropdown value
            if student.classes and student.classes not in classes_list:
                student.classes = random.choice(classes_list)
                print(f"Updated {student.username} classes from '{student.classes}' to '{student.classes}'")
            
            updated_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\nSuccessfully updated {updated_count} students!")
            print("All students now have values that match the dropdown options.")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating students: {e}")

if __name__ == "__main__":
    update_existing_students() 