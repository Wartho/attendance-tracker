#!/usr/bin/env python3
"""
Script to check for and fix students with Orange belt color.
"""

from app import create_app, db
from app.models import User
import random

def check_and_fix_orange():
    app = create_app()
    
    with app.app_context():
        # Find students with Orange belt
        orange_students = User.query.filter_by(role='student', belt_level='Orange').all()
        
        if orange_students:
            print(f"Found {len(orange_students)} students with Orange belt:")
            for student in orange_students:
                print(f"  - {student.first_name} {student.last_name}")
            
            # Valid belt colors (excluding Orange)
            valid_colors = ["White", "Yellow", "Green", "Purple", "Purple-Blue", "Blue", "Blue-Brown", "Brown", "Brown-Red", "Red", "Red-Black", "Black"]
            
            # Fix each student
            for student in orange_students:
                new_color = random.choice(valid_colors)
                print(f"Changing {student.first_name} {student.last_name} from Orange to {new_color}")
                student.belt_level = new_color
            
            db.session.commit()
            print(f"\nFixed {len(orange_students)} students with Orange belt.")
        else:
            print("No students found with Orange belt.")
        
        # Show all students and their belt colors
        print("\nAll students and their belt colors:")
        all_students = User.query.filter_by(role='student').all()
        for student in all_students:
            print(f"  {student.first_name} {student.last_name}: {student.belt_level}")

if __name__ == '__main__':
    check_and_fix_orange() 