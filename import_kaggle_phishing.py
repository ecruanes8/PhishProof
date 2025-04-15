import csv
import sqlite3
import uuid
from datetime import datetime
import json
import sys

# Increase the field size limit
csv.field_size_limit(sys.maxsize)

# === CONFIG ===
CSV_FILE = "SpamAssasin.csv"  # <- change to the file you want to import
DB_FILE = "converted_emails.db"

# === Create compatible schema ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            thread_id TEXT,
            label_ids TEXT,
            snippet TEXT,
            internal_date INTEGER,
            from_email TEXT,
            to_email TEXT,
            subject TEXT,
            date TEXT,
            body TEXT,
            headers TEXT,
            suspicion_score REAL,
            classification TEXT
        )
    ''')
    conn.commit()
    conn.close()

# === Read and insert data ===
def import_kaggle_csv(csv_file):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email_id = str(uuid.uuid4())
            thread_id = ""
            label_ids = json.dumps([])
            body = row.get("email", "")
            snippet = body[:150]
            internal_date = int(datetime.now().timestamp())
            from_email = "unknown"
            to_email = "unknown"
            subject = row.get("subject", "")
            date = datetime.now().isoformat()
            headers = json.dumps({})
            suspicion_score = None

            # Numeric label: 1 = phishing, 0 = safe
            raw_label = str(row.get("label", "")).strip()
            if raw_label == "1":
                classification = "phishing"
            elif raw_label == "0":
                classification = "safe"
            else:
                classification = "suspicious"

            cursor.execute('''
                INSERT INTO emails (
                    id, thread_id, label_ids, snippet, internal_date,
                    from_email, to_email, subject, date, body, headers,
                    suspicion_score, classification
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_id, thread_id, label_ids, snippet, internal_date,
                from_email, to_email, subject, date, body, headers,
                suspicion_score, classification
            ))

    conn.commit()
    conn.close()
    print(f"✅ Imported emails from {csv_file} into {DB_FILE}")

# === Run all ===
if __name__ == "__main__":
    init_db()
    import_kaggle_csv(CSV_FILE)
