#!/usr/bin/env python3
"""
Script to add 48 dummy students for testing purposes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import random
from datetime import date, timedelta

def generate_dummy_students():
    app = create_app()
    
    with app.app_context():
        # Check if we already have students
        existing_students = User.query.filter_by(role='student').count()
        print(f"Found {existing_students} existing students")
        
        # Generate 48 new students
        students_to_add = 48
        
        # Sample data for realistic student generation
        first_names = [
            "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Isabella", "Lucas", "Sophia", "Mason",
            "Mia", "Oliver", "Charlotte", "Elijah", "Amelia", "James", "Harper", "Benjamin", "Evelyn", "Sebastian",
            "Abigail", "Michael", "Emily", "Daniel", "Elizabeth", "Henry", "Sofia", "Jackson", "Avery", "Samuel",
            "Ella", "David", "Madison", "Joseph", "Scarlett", "Christopher", "Victoria", "Andrew", "Luna", "Joshua",
            "Grace", "Wyatt", "Chloe", "John", "Penelope", "Jack", "Layla", "Luke", "Riley", "Anthony"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
            "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
        ]
        
        programs = ["3 months", "6 months", "1 year"]
        plans = ["1/week", "2/week"]
        classes_list = ["48", "96"]
        belt_levels = ["White", "Yellow", "Green", "Purple", "Purple-Blue", "Blue", "Blue-Brown", "Brown", "Brown-Red", "Red", "Red-Black", "Black"]
        gender_options = ["Male", "Female", "Other"]
        
        # Generate students
        for i in range(students_to_add):
            # Generate unique username
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(10, 99)}"
            
            # Check if username already exists
            while User.query.filter_by(username=username).first():
                username = f"{first_name.lower()}{last_name.lower()}{random.randint(10, 99)}"
            
            # Generate email
            email = f"{username}@example.com"
            
            # Generate random date of birth (ages 5-18 for most students)
            age = random.randint(5, 18)
            birth_year = date.today().year - age
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Using 28 to avoid month/day issues
            date_of_birth = date(birth_year, birth_month, birth_day)
            
            # Generate random effective dates
            effective_start = date.today() - timedelta(days=random.randint(0, 365))
            effective_end = effective_start + timedelta(days=random.randint(30, 365))
            
            # Create student
            student = User(
                username=username,
                email=email,
                password_hash=generate_password_hash("password123"),
                role="student",
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=random.choice(gender_options),
                program=random.choice(programs),
                plan=random.choice(plans),
                classes=random.choice(classes_list),
                phone_number=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                belt_level=random.choice(belt_levels),
                effective_from=effective_start,
                effective_to=effective_end
            )
            
            db.session.add(student)
            print(f"Added student: {first_name} {last_name} ({username})")
        
        # Commit all changes
        db.session.commit()
        print(f"\nSuccessfully added {students_to_add} dummy students!")
        print(f"Total students in database: {User.query.filter_by(role='student').count()}")

if __name__ == "__main__":
    generate_dummy_students() 