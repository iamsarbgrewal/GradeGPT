import sqlite3

def main():
    conn = sqlite3.connect('gradegpt.db', check_same_thread=False)
    cur = conn.cursor()
    cur.executescript("""CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        student_id INTEGER,
        answer_text TEXT,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );CREATE TABLE IF NOT EXISTS model (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        answer_text TEXT,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT
    )""")
    cur.close()


if __name__ == '__main__':
    main()
