from abc import ABC, abstractmethod
from typing import List, Optional
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- Generic Email Client Interface ---
class EmailClient(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> None:
        pass

    @abstractmethod
    def read_emails(self, query: str = "") -> List[dict]:
        pass

# --- Gmail Implementation ---
class GmailClient(EmailClient):
    def __init__(self, creds):
        from googleapiclient.discovery import build
        self.service = build('gmail', 'v1', credentials=creds)

    def send_email(self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> None:
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        if attachments:
            for file_path in attachments:
                part = MIMEBase('application', 'octet-stream')
                with open(file_path, 'rb') as f:
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        self.service.users().messages().send(userId='me', body={'raw': raw}).execute()

    def read_emails(self, query: str = "") -> List[dict]:
        results = self.service.users().messages().list(userId='me', q=query, maxResults=10).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages:
            msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
            snippet = msg_data.get('snippet', '')
            emails.append({'id': msg['id'], 'snippet': snippet})
        return emails

# --- Usage Example (requires Google API credentials) ---
# from google.oauth2.credentials import Credentials
# creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.modify'])
# client = GmailClient(creds)
# client.send_email('recipient@example.com', 'Test Subject', 'Hello from GmailClient!')
# emails = client.read_emails('is:unread')
# print(emails) 