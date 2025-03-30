import sqlite3
import json
from datetime import datetime

def print_email(email):
    print("\n" + "="*80)
    print(f"EMAIL ID: {email[0]}")
    print(f"THREAD ID: {email[1]}")
    print(f"DATE: {email[8]}")
    print(f"FROM: {email[5]}")
    print(f"TO: {email[6]}")
    print(f"SUBJECT: {email[7]}")
    print("-"*80)
    print(f"SNIPPET: {email[3]}")
    print("-"*80)
    
    # Print labels if they exist
    labels = json.loads(email[2])
    if labels:
        print(f"LABELS: {', '.join(labels)}")
    
    # Print headers if needed
    headers = json.loads(email[10])
    print("\nHEADERS:")
    for key, value in headers.items():
        print(f"{key}: {value}")
    
    print("\nBODY:")
    print(email[9])
    print("="*80 + "\n")

def list_emails():
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM emails")
    total = cursor.fetchone()[0]
    print(f"\nFound {total} emails in database\n")
    
    # Get all emails sorted by date (newest first)
    cursor.execute("""
        SELECT id, thread_id, label_ids, snippet, internal_date, 
               from_email, to_email, subject, date, body, headers
        FROM emails
        ORDER BY internal_date DESC
    """)
    
    while True:
        print("\nOptions:")
        print("1. View next email")
        print("2. Search emails")
        print("3. Quit")
        choice = input("Enter your choice: ")
        
        if choice == '1':
            email = cursor.fetchone()
            if email:
                print_email(email)
            else:
                print("No more emails in database!")
                cursor.execute("""
                    SELECT id, thread_id, label_ids, snippet, internal_date, 
                           from_email, to_email, subject, date, body, headers
                    FROM emails
                    ORDER BY internal_date DESC
                """)
                email = cursor.fetchone()
                if email:
                    print_email(email)
                
        elif choice == '2':
            search_term = input("Enter search term (subject/from/to/body): ")
            cursor.execute("""
                SELECT id, thread_id, label_ids, snippet, internal_date, 
                       from_email, to_email, subject, date, body, headers
                FROM emails
                WHERE subject LIKE ? OR from_email LIKE ? OR to_email LIKE ? OR body LIKE ?
                ORDER BY internal_date DESC
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            results = cursor.fetchall()
            print(f"\nFound {len(results)} matching emails")
            for email in results:
                print(f"{email[8]} | From: {email[5]} | Subject: {email[7]}")
                
            if results:
                view = input("\nView first matching email? (y/n): ")
                if view.lower() == 'y':
                    print_email(results[0])
        
        elif choice == '3':
            break
            
        else:
            print("Invalid choice, please try again")
    
    conn.close()

if __name__ == '__main__':
    list_emails()