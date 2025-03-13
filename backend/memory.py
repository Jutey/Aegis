import sqlite3

# Initialize database
conn = sqlite3.connect('database/assistant_memory.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY,
        topic TEXT,
        detail TEXT
    )
''')
conn.commit()

def remember(topic, detail):
    cursor.execute('INSERT INTO memory (topic, detail) VALUES (?, ?)', (topic, detail))
    conn.commit()

def recall(topic):
    cursor.execute('SELECT detail FROM memory WHERE topic = ?', (topic,))
    result = cursor.fetchone()
    return result[0] if result else None
