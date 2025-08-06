#!/usr/bin/env python3
"""
Script to set effective dates for students who don't have them
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from datetime import datetime, timedelta
import random

def set_effective_dates():
    app = create_app()
    
    with app.app_context():
        # Get students without effective_from dates
        students_without_dates = User.query.filter_by(role='student').filter(
            (User.effective_from.is_(None)) | (User.effective_from == '')
        ).all()
        
        print(f"Found {len(students_without_dates)} students without effective dates")
        
        if not students_without_dates:
            print("All students already have effective dates set!")
            return
        
        # Set effective dates for students
        for student in students_without_dates:
            # Set effective_from to a random date within the last 6 months
            days_ago = random.randint(0, 180)
            effective_from = datetime.now().date() - timedelta(days=days_ago)
            
            # Set effective_to based on program
            if student.program == "3 months":
                effective_to = effective_from + timedelta(days=90)
            elif student.program == "6 months":
                effective_to = effective_from + timedelta(days=180)
            elif student.program == "1 year":
                effective_to = effective_from + timedelta(days=365)
            else:
                # Default to 6 months if no program set
                effective_to = effective_from + timedelta(days=180)
            
            student.effective_from = effective_from
            student.effective_to = effective_to
            
            print(f"Set {student.username} effective dates: {effective_from} to {effective_to}")
        
        # Commit changes
        try:
            db.session.commit()
            print(f"\nSuccessfully set effective dates for {len(students_without_dates)} students!")
        except Exception as e:
            db.session.rollback()
            print(f"Error setting effective dates: {e}")

if __name__ == "__main__":
    set_effective_dates() 