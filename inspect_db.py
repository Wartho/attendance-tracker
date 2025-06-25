import sqlite3
import os

# Get the database path
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'app.db')

print(f"Database path: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get table info
    c.execute('PRAGMA table_info(user)')
    columns = c.fetchall()
    
    print("\nUser table schema:")
    print("cid | name | type | notnull | dflt_value | pk")
    print("-" * 50)
    for col in columns:
        print(f"{col[0]} | {col[1]} | {col[2]} | {col[3]} | {col[4]} | {col[5]}")
    
    # Get sample data
    c.execute('SELECT * FROM user LIMIT 3')
    rows = c.fetchall()
    
    print(f"\nSample data (first 3 rows):")
    for row in rows:
        print(row)
    
    conn.close()
else:
    print("Database file not found!") 