#!/usr/bin/env python3
"""
Script to fix invalid belt colors in the database.
This script will replace any invalid belt colors with valid ones.
"""

from app import create_app, db
from app.models import User
import random

def fix_belt_colors():
    app = create_app()
    
    with app.app_context():
        # Valid belt colors
        valid_belt_colors = [
            "White", "Yellow", "Green", "Purple", "Purple-Blue", 
            "Blue", "Blue-Brown", "Brown", "Brown-Red", "Red", 
            "Red-Black", "Black", "Not Set", "No Belt"
        ]
        
        # Find students with invalid belt colors
        students = User.query.filter_by(role='student').all()
        fixed_count = 0
        
        for student in students:
            if student.belt_level not in valid_belt_colors:
                print(f"Fixing student {student.first_name} {student.last_name}: {student.belt_level} -> ", end="")
                
                # Replace invalid belt color with a random valid one (excluding "Not Set" and "No Belt")
                valid_colors = [color for color in valid_belt_colors if color not in ["Not Set", "No Belt"]]
                new_belt_color = random.choice(valid_colors)
                
                student.belt_level = new_belt_color
                print(f"{new_belt_color}")
                fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"\nFixed {fixed_count} students with invalid belt colors.")
        else:
            print("No students with invalid belt colors found.")
        
        # Show summary
        print(f"\nTotal students in database: {User.query.filter_by(role='student').count()}")
        
        # Show belt color distribution
        print("\nBelt color distribution:")
        for color in valid_belt_colors:
            count = User.query.filter_by(role='student', belt_level=color).count()
            if count > 0:
                print(f"  {color}: {count}")

if __name__ == '__main__':
    fix_belt_colors() 