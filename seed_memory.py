import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'aira_memory.db'
memories = [
    {'days_ago': 3, 'summary': 'Harris and AIRA discussed the 14-week development roadmap.'
                              ' They agreed on local-first until Phase 8 for privacy.'},
    {'days_ago': 2, 'summary': 'The conversation focused on the human-like friend persona.'
                              ' Harris emphasised grounded and supportive over robotic.'},
    {'days_ago': 1, 'summary': 'Harris mentioned getting a new laptop for Gemma 4 E4B.'
                              ' Phase 1 integration planned for the day of arrival.'},
]

def seed():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS session_summaries
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             timestamp TEXT NOT NULL, summary TEXT NOT NULL)''')
        conn.execute('DELETE FROM session_summaries')
        for m in memories:
            ts = (datetime.now() - timedelta(days=m['days_ago'])).isoformat()
            conn.execute('INSERT INTO session_summaries (timestamp, summary) VALUES (?,?)',
                         (ts, m['summary']))
        conn.commit()
    print(f'Seeded {len(memories)} memories into {DB_PATH}')

if __name__ == '__main__': seed()
