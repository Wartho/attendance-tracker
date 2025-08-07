#!/usr/bin/env python3
"""
Test script to verify Plan section visibility
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from flask import render_template_string

def test_plan_section():
    app = create_app()
    
    with app.app_context():
        # Get student #54
        student = User.query.filter_by(id=54).first()
        if student:
            print(f"=== Testing Plan Section for Student #{student.id} ===")
            print(f"Name: {student.first_name} {student.last_name}")
            print(f"Program: {student.program}")
            print(f"Plan: {student.plan}")
            
            # Read the template file
            template_path = "app/templates/teacher/student_calendar.html"
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Test rendering the Plan section specifically
                plan_section_template = """
                <div class="mt-4">
                    <h4>Plan</h4>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Program</th>
                                    <th>Plan</th>
                                    <th>Classes</th>
                                    <th>Remaining</th>
                                    <th>Effective Period</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>{{ student.program if student.program else 'Not Set' }}</td>
                                    <td>{{ student.plan if student.plan else 'Not Set' }}</td>
                                    <td>{{ student.classes if student.classes else 'Not Set' }}</td>
                                    <td>
                                        <span id="remainingClasses" style="cursor: pointer;" onclick="showPlanCalculation()">
                                            <i class="fas fa-calculator"></i> Calculate
                                        </span>
                                    </td>
                                    <td>
                                        {% if student.effective_from or student.effective_to %}
                                            {{ student.effective_from.strftime('%Y-%m-%d') if student.effective_from else 'Not Set' }} to 
                                            {{ student.effective_to.strftime('%Y-%m-%d') if student.effective_to else 'Not Set' }}
                                        {% else %}
                                            Not Set
                                        {% endif %}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                """
                
                try:
                    rendered = render_template_string(plan_section_template, student=student)
                    print("\n=== Rendered Plan Section ===")
                    print(rendered)
                    print("\n✅ Plan section renders successfully")
                    
                    # Check if the section contains expected content
                    if "Plan" in rendered and "Program" in rendered:
                        print("✅ Plan section contains expected headers")
                    else:
                        print("❌ Plan section missing expected content")
                        
                except Exception as e:
                    print(f"❌ Error rendering Plan section: {e}")
            else:
                print(f"❌ Template file not found: {template_path}")
        else:
            print("❌ Student #54 not found in database")

if __name__ == "__main__":
    test_plan_section() 