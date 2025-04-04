import os.path
import json
import sqlite3
from datetime import datetime
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes needed for reading email contents + metadata
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]


# Database setup
def init_db():
    connection = sqlite3.connect('emails.db')
    cursor = connection.cursor()
    # Create database containing all email info
    cursor.execute('''CREATE TABLE IF NOT EXISTS emails
                 (id TEXT PRIMARY KEY,
                  thread_id TEXT,
                  label_ids TEXT,
                  snippet TEXT,
                  internal_date INTEGER,
                  from_email TEXT,
                  to_email TEXT,
                  subject TEXT,
                  date TEXT,
                  body TEXT,
                  headers TEXT)''')
    cursor.execute('''ALTER TABLE emails ADD COLUMN suspicion_score REAL''')
    cursor.execute('''ALTER TABLE emails ADD COLUMN classification TEXT''')

    connection.commit()
    connection.close()


def store_email(service, message_id):
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = {header['name']: header['value'] for header in message['payload']['headers']}
        
        # Extract basic info
        subject = headers.get('Subject', '')
        from_email = headers.get('From', '')
        to_email = headers.get('To', '')
        date = headers.get('Date', '')
        
        # Convert date to timestamp if available
        if date:
            try:
                date_parsed = parsedate_to_datetime(date)
                date_str = date_parsed.isoformat()
            except:
                date_str = date
        else:
            date_str = ''
        
        # Get body content
        body = ''
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body += part['body'].get('data', '')
                elif part['mimeType'] == 'text/html':
                    body += part['body'].get('data', '')
        else:
            body = message['payload']['body'].get('data', '')
        
        # Decode base64 body if needed
        if body:
            import base64
            body = base64.urlsafe_b64decode(body).decode('utf-8', errors='ignore')
        
        # Store in database
        connection = sqlite3.connect('emails.db')
        cursor = connection.cursor()
        
        cursor.execute('''INSERT OR IGNORE INTO emails 
                     (id, thread_id, label_ids, snippet, internal_date, 
                      from_email, to_email, subject, date, body, headers)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (message['id'],
                  message['threadId'],
                  json.dumps(message.get('labelIds', [])),
                  message.get('snippet', ''),
                  int(message['internalDate']),
                  from_email,
                  to_email,
                  subject,
                  date_str,
                  body,
                  json.dumps(headers)))
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error processing message {message_id}: {str(e)}")


def get_all_emails(service):
    try:
        # Get all message IDs
        results = service.users().messages().list(
            userId='me',
            includeSpamTrash=False,
            maxResults=500
        ).execute()
        
        messages = results.get('messages', [])
        
        while 'nextPageToken' in results:
            page_token = results['nextPageToken']
            results = service.users().messages().list(
                userId='me',
                includeSpamTrash=False,
                maxResults=500,
                pageToken=page_token
            ).execute()
            messages.extend(results.get('messages', []))
        
        # Process each message
        for message in messages:
            store_email(service, message['id'])
            print(f"Processed message {message['id']}")
            
    except HttpError as error:
        print(f"An error occurred: {error}")


def main():
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except json.JSONDecodeError:
            os.remove('token.json')
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        init_db()
        get_all_emails(service)
        print("Email import completed successfully!")
        
    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == '__main__':
    main()