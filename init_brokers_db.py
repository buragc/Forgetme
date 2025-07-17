import sqlite3

DB_NAME = 'brokers.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS brokers (
            brokerID INTEGER PRIMARY KEY AUTOINCREMENT,
            brokerName TEXT NOT NULL,
            brokerURL TEXT NOT NULL,
            removalState TEXT DEFAULT 'Not Submitted',
            submissionDate TEXT,
            confirmationDate TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_broker(brokerName, brokerURL, submissionDate=None, confirmationDate=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO brokers (brokerName, brokerURL, submissionDate, confirmationDate)
        VALUES (?, ?, ?, ?)
    ''', (brokerName, brokerURL, submissionDate, confirmationDate))
    conn.commit()
    conn.close()

def reset_broker_submission(broker_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE brokers
        SET removalState = 'Not Requested',
            submissionDate = NULL
        WHERE brokerID = ?
    ''', (broker_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    reset_broker_submission(1)
    insert_broker('peoplebyname', 'https://www.peoplebyname.com/contact.php', None, None)
    print(f"Database '{DB_NAME}' initialized with table 'brokers' and inserted 'peoplebyname'.") 