import sqlite3
from tabulate import tabulate

conn = sqlite3.connect('attendance-tracker/instance/app.db')
c = conn.cursor()

c.execute('PRAGMA table_info(user)')
columns = [col[1] for col in c.fetchall()]

c.execute('SELECT * FROM user')
rows = c.fetchall()

print(tabulate(rows, headers=columns, tablefmt='psql'))

conn.close() 