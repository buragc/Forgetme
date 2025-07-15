import unittest
from unittest.mock import MagicMock, patch
from email_client import EmailClient, GmailClient
import os

class DummyCreds:
    pass

class TestEmailClient(unittest.TestCase):
    def test_email_client_interface(self):
        # EmailClient is abstract, cannot instantiate directly
        with self.assertRaises(TypeError):
            EmailClient()

    @patch('googleapiclient.discovery.build')
    def test_gmail_client_send_email(self, mock_build):
        # Mock Gmail API service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        creds = DummyCreds()
        client = GmailClient(creds)
        # Patch the send method
        mock_send = mock_service.users().messages().send
        mock_send.return_value.execute.return_value = {'id': '123'}
        # Should not raise
        client.send_email('to@example.com', 'Subject', 'Body')
        self.assertTrue(mock_send.called)

    @patch('googleapiclient.discovery.build')
    def test_gmail_client_read_emails(self, mock_build):
        # Mock Gmail API service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        creds = DummyCreds()
        client = GmailClient(creds)
        # Mock list and get
        mock_list = mock_service.users().messages().list
        mock_list.return_value.execute.return_value = {'messages': [{'id': 'abc'}]}
        mock_get = mock_service.users().messages().get
        mock_get.return_value.execute.return_value = {'snippet': 'Hello!'}
        emails = client.read_emails('is:unread')
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['snippet'], 'Hello!')

    def test_gmail_client_integration_send_email(self):
        """
        Integration test: Actually sends an email to echo@gmail.com with subject and body 'TEST'.
        Requires valid Gmail API credentials in environment variables or .env file.
        """
        from google.oauth2.credentials import Credentials
        from dotenv import load_dotenv
        load_dotenv()
        creds = Credentials(
            None,
            refresh_token=os.getenv('GMAIL_REFRESH_TOKEN'),
            client_id=os.getenv('GMAIL_CLIENT_ID'),
            client_secret=os.getenv('GMAIL_CLIENT_SECRET'),
            token_uri='https://oauth2.googleapis.com/token',
        )
        client = GmailClient(creds)
        try:
            client.send_email('echo@gmail.com', 'TEST', 'TEST')
            print('Integration email sent successfully.')
        except Exception as e:
            self.fail(f'Integration email send failed: {e}')

if __name__ == '__main__':
    unittest.main() 