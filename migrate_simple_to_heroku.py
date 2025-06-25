import os
import sqlite3
import datetime
import uuid
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

# Local SQLite DB path
LOCAL_DB = 'instance/app.db'  # Database with actual data
# Heroku Postgres URL
HEROKU_DB = 'postgres://ubfrspoi93klk9:pc9fbefc60f593eeb9fe6b1fef74e4189255b577406e51c48e56a95adba91ec1d@cer3tutrbi7n1t.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/ddll5a5crrf8sp'
if HEROKU_DB.startswith('postgres://'):
    HEROKU_DB = HEROKU_DB.replace('postgres://', 'postgresql://', 1)

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), nullable=False)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    password_hash = Column(String(128))
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime)
    qr_code_id = Column(String(36), unique=True)

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)

# Helper to fetch all rows from a table
def fetch_all(conn, table):
    c = conn.cursor()
    try:
        c.execute(f'SELECT * FROM {table}')
        return c.fetchall(), [desc[0] for desc in c.description]
    except sqlite3.OperationalError as e:
        print(f"Table {table} does not exist or is empty: {e}")
        return [], []

def migrate_table(local_rows, columns, Model, session, unique_fields=None):
    inserted = 0
    for row in local_rows:
        data = dict(zip(columns, row))
        # Remove any fields not in Model
        model_fields = {c.name for c in Model.__table__.columns}
        data = {k: v for k, v in data.items() if k in model_fields}
        obj = Model(**data)
        try:
            if unique_fields:
                # Try to find existing by unique fields
                query = {f: data[f] for f in unique_fields if f in data}
                exists = session.query(Model).filter_by(**query).first()
                if exists:
                    continue
            session.merge(obj)
            session.commit()
            inserted += 1
        except Exception as e:
            session.rollback()
            print(f"Error inserting {Model.__tablename__}: {e}")
    print(f"{Model.__tablename__}: Inserted/updated {inserted} records.")

def main():
    conn = sqlite3.connect(LOCAL_DB)
    heroku_engine = create_engine(HEROKU_DB)
    Session = sessionmaker(bind=heroku_engine)
    session = Session()

    # Only migrate tables that exist in Heroku: user and attendance
    tables = [
        ('user', User, ['username']),
        ('attendance', Attendance, ['student_id', 'date'])
    ]
    
    for table, Model, unique_fields in tables:
        print(f"Migrating {table}...")
        rows, columns = fetch_all(conn, table)
        if rows:
            migrate_table(rows, columns, Model, session, unique_fields)
        else:
            print(f"No data found in {table}")
    
    session.close()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    main() 