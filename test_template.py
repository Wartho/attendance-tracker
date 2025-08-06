#!/usr/bin/env python3
"""
Test script to verify template structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def test_template():
    app = create_app()
    
    with app.app_context():
        # Get a student to test with
        student = User.query.filter_by(role='student').first()
        if student:
            print(f"Testing with student: {student.first_name} {student.last_name}")
            print(f"Program: {student.program}")
            print(f"Plan: {student.plan}")
            print(f"Classes: {student.classes}")
            print(f"Effective from: {student.effective_from}")
            print(f"Effective to: {student.effective_to}")
            
            # Check if the template file exists and contains the Plan section
            template_path = "app/templates/teacher/student_calendar.html"
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'personalInfoDisplay2' in content:
                        print("✅ Plan section found in template")
                    else:
                        print("❌ Plan section not found in template")
                    
                    if 'Program:' in content:
                        print("✅ Program field found in template")
                    else:
                        print("❌ Program field not found in template")
                    
                    if 'Plan:' in content:
                        print("✅ Plan field found in template")
                    else:
                        print("❌ Plan field not found in template")
            else:
                print(f"❌ Template file not found: {template_path}")
        else:
            print("No students found in database")

if __name__ == "__main__":
    test_template() 