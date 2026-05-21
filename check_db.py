import sys, io, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
conn = sqlite3.connect('history.db')
c = conn.cursor()
c.execute('SELECT source, data FROM results JOIN searches ON results.job_id = searches.job_id ORDER BY results.ROWID DESC LIMIT 20')
for row in c.fetchall():
    print(row[0], row[1])
