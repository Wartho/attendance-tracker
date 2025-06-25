import os
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Date, Text, Boolean, ForeignKey, Time
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

# Heroku Postgres URL
HEROKU_DB = 'postgres://ubfrspoi93klk9:pc9fbefc60f593eeb9fe6b1fef74e4189255b577406e51c48e56a95adba91ec1d@cer3tutrbi7n1t.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/ddll5a5crrf8sp'
if HEROKU_DB.startswith('postgres://'):
    HEROKU_DB = HEROKU_DB.replace('postgres://', 'postgresql://', 1)

def update_heroku_schema():
    engine = create_engine(HEROKU_DB)
    
    with engine.connect() as conn:
        # Add missing columns to user table
        print("Adding missing columns to user table...")
        try:
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(255)"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS belt_level VARCHAR(20) DEFAULT 'Not Set'"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS date_of_birth DATE"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS gender VARCHAR(10)"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS program VARCHAR(20)"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS plan VARCHAR(20)"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS effective_from DATE"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS effective_to DATE"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS classes VARCHAR(10)"))
            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20)"))
            conn.commit()
            print("✅ User table updated")
        except Exception as e:
            print(f"Error updating user table: {e}")
            conn.rollback()

        # Add missing columns to attendance table
        print("Adding missing columns to attendance table...")
        try:
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"))
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS class_id INTEGER"))
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_in_time TIME"))
            conn.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS check_in_method VARCHAR(20)"))
            conn.commit()
            print("✅ Attendance table updated")
        except Exception as e:
            print(f"Error updating attendance table: {e}")
            conn.rollback()

        # Create belt_history table
        print("Creating belt_history table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS belt_history (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER NOT NULL REFERENCES "user"(id),
                    belt_level VARCHAR(20) NOT NULL,
                    date_obtained DATE NOT NULL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Belt history table created")
        except Exception as e:
            print(f"Error creating belt_history table: {e}")
            conn.rollback()

        # Create class table
        print("Creating class table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS "class" (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    day_of_week INTEGER NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    min_belt_level VARCHAR(50),
                    max_belt_level VARCHAR(50),
                    max_capacity INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Class table created")
        except Exception as e:
            print(f"Error creating class table: {e}")
            conn.rollback()

        # Create class_enrollment table
        print("Creating class_enrollment table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS class_enrollment (
                    id SERIAL PRIMARY KEY,
                    class_id INTEGER NOT NULL REFERENCES "class"(id),
                    student_id INTEGER NOT NULL REFERENCES "user"(id),
                    enrolled_from DATE NOT NULL,
                    enrolled_until DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Class enrollment table created")
        except Exception as e:
            print(f"Error creating class_enrollment table: {e}")
            conn.rollback()

        # Create class_holiday table
        print("Creating class_holiday table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS class_holiday (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    description VARCHAR(200),
                    is_recurring BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Class holiday table created")
        except Exception as e:
            print(f"Error creating class_holiday table: {e}")
            conn.rollback()

        # Add foreign key constraint for attendance.class_id
        print("Adding foreign key constraints...")
        try:
            conn.execute(text("""
                ALTER TABLE attendance 
                ADD CONSTRAINT IF NOT EXISTS fk_attendance_class_id 
                FOREIGN KEY (class_id) REFERENCES "class"(id)
            """))
            conn.commit()
            print("✅ Foreign key constraints added")
        except Exception as e:
            print(f"Error adding foreign key constraints: {e}")
            conn.rollback()

    print("\n🎉 Database schema update complete!")

if __name__ == '__main__':
    update_heroku_schema() 