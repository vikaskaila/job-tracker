import sqlite3
import os

db_path = os.path.join(os.environ.get('APPDATA'), 'JobTracker', 'jobs.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check columns
cursor.execute('PRAGMA table_info(jobs)')
columns = cursor.fetchall()
print('Database columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

print('\nSample jobs:')
cursor.execute('SELECT title, LENGTH(COALESCE(description, "")), company FROM jobs LIMIT 5')
rows = cursor.fetchall()
for row in rows:
    print(f'  Title: {row[0][:50]}... | Desc Length: {row[1]} | Company: {row[2]}')

# Check if descriptions have content
print('\nDescription statistics:')
cursor.execute('''
    SELECT 
        COUNT(*) as total_jobs,
        SUM(CASE WHEN description IS NULL OR description = '' THEN 1 ELSE 0 END) as empty_desc,
        SUM(CASE WHEN description IS NOT NULL AND description != '' THEN 1 ELSE 0 END) as filled_desc
    FROM jobs
''')
stats = cursor.fetchone()
print(f'  Total jobs: {stats[0]}')
print(f'  Jobs with empty description: {stats[1]}')
print(f'  Jobs with description: {stats[2]}')

conn.close()
