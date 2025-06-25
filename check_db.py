import sqlite3

def check_db(db_path):
    print(f"\nChecking {db_path}:")
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in c.fetchall()]
        print(f"Tables: {tables}")
        
        for table in tables:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            print(f"  {table}: {count} records")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

# Check all database files
check_db('app.db')
check_db('instance/app.db')
check_db('instance/attendance.db') 