from app import create_app, db
from app.models import User
import sqlite3

app = create_app()

with app.app_context():
    # Get the database path
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    
    # Get indexes
    cursor.execute("PRAGMA index_list(user)")
    indexes = cursor.fetchall()
    
    print("\nTable Structure:")
    for col in columns:
        print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")
    
    print("\nUnique Indexes:")
    for idx in indexes:
        if idx[2]:  # if index is unique
            print(f"Index: {idx[1]}")
            # Get index columns
            cursor.execute(f"PRAGMA index_info({idx[1]})")
            index_cols = cursor.fetchall()
            for col in index_cols:
                cursor.execute("PRAGMA table_info(user)")
                table_cols = cursor.fetchall()
                col_idx = col[2]  # column index in the table
                if col_idx < len(table_cols):
                    print(f"  - Column: {table_cols[col_idx][1]}")
    
    conn.close() 