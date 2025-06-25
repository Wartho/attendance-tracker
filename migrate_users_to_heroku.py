import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import sqlite3
import datetime
import uuid

# Local SQLite DB path
LOCAL_DB = 'app.db'
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    qr_code_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

# 1. Read users from local SQLite
def fetch_local_users():
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, first_name, last_name, password_hash, role, created_at, qr_code_id FROM user')
    users = cursor.fetchall()
    conn.close()
    return users

# 2. Insert users into Heroku Postgres
def migrate_users():
    local_users = fetch_local_users()
    print(f"Found {len(local_users)} users in local DB.")
    heroku_engine = create_engine(HEROKU_DB)
    Session = sessionmaker(bind=heroku_engine)
    session = Session()
    inserted = 0
    skipped = 0
    for u in local_users:
        user = User(
            id=u[0],
            username=u[1],
            email=u[2],
            first_name=u[3],
            last_name=u[4],
            password_hash=u[5],
            role=u[6],
            created_at=u[7],
            qr_code_id=u[8]
        )
        try:
            session.merge(user)  # merge will insert or update by primary key
            session.commit()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    print(f"Inserted or updated {inserted} users. Skipped {skipped}.")
    session.close()

if __name__ == '__main__':
    migrate_users() 