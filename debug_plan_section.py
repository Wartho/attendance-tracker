#!/usr/bin/env python3
"""
Debug script to check Plan section visibility
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def debug_plan_section():
    app = create_app()
    
    with app.app_context():
        # Get student #54
        student = User.query.filter_by(id=54).first()
        if student:
            print(f"=== Student #{student.id} Debug Info ===")
            print(f"Name: {student.first_name} {student.last_name}")
            print(f"Program: {student.program}")
            print(f"Plan: {student.plan}")
            print(f"Classes: {student.classes}")
            print(f"Effective from: {student.effective_from}")
            print(f"Effective to: {student.effective_to}")
            print(f"Belt level: {student.belt_level}")
            
            # Check if the template file exists and contains the Plan section
            template_path = "app/templates/teacher/student_calendar.html"
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    print(f"\n=== Template Analysis ===")
                    if 'personalInfoDisplay2' in content:
                        print("✅ Plan section (personalInfoDisplay2) found in template")
                    else:
                        print("❌ Plan section NOT found in template")
                    
                    if 'Program:' in content:
                        print("✅ Program field found in template")
                    else:
                        print("❌ Program field NOT found in template")
                    
                    if 'Plan:' in content:
                        print("✅ Plan field found in template")
                    else:
                        print("❌ Plan field NOT found in template")
                    
                    # Check for JavaScript that might hide the section
                    if 'display: none' in content:
                        print("⚠️  Found 'display: none' in template - might be hiding content")
                    
                    # Check for CSS classes that might affect visibility
                    if 'd-flex justify-content-between' in content:
                        print("✅ Found flexbox classes for layout")
                    
            else:
                print(f"❌ Template file not found: {template_path}")
        else:
            print("❌ Student #54 not found in database")

if __name__ == "__main__":
    debug_plan_section() 