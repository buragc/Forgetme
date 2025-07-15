from __future__ import print_function
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying scopes, delete the token.json file
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def main():
    creds = None
    # Load saved tokens if they exist
    if os.path.exists('tokens.json'):
        creds = Credentials.from_authorized_user_file('tokens.json', SCOPES)
    
    # If there are no valid credentials, start the login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # <-- uses refresh token automatically
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_gmail.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the access and refresh tokens to a file
        with open('tokens.json', 'w') as token:
            token.write(creds.to_json())

    print("Access token:", creds.token)
    print("Refresh token:", creds.refresh_token)

if __name__ == '__main__':
    main()