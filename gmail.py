import os.path
import base64
import datetime
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]



def get_gmail_messages(query, max_results=10):
    """Get a list of Gmail messages matching the query."""
    creds = None
    if os.path.exists(f"{config.get_gmail_credential_folder()}token.json"):
        creds = Credentials.from_authorized_user_file(f"{config.get_gmail_credential_folder()}token.json", SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds:
        print("No valid credentials found. Please authenticate first.")
        return []

    service = build("gmail", "v1", credentials=creds)
    return get_messages(service, query, max_results)



def get_messages(service, query,max_results=10):
    """Get a list of messages matching the query."""
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages_info = results.get('messages', [])
        emails_data = []

        if not messages_info:
            print("No messages found matching your query.")
            return emails_data

        for msg_info in messages_info:
            msg = service.users().messages().get(userId='me', id=msg_info['id']).execute()
            labels = msg.get('labelIds', [])
            labels.sort()
            snippet = msg.get('snippet')
            # print(f' Message --- {msg}')
            payload = msg.get('payload', {})
            # print(f'Payload --- {payload}')
            headers = payload.get('headers', [])
            # print(f'Headers --- {headers}')
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'N/A')
            emaildate = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'N/A')
            emailfrom = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'N/A')
            emailto = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'N/A')
            
            body_html = None
            body_text = None

            if 'parts' in payload:
                for part in payload['parts']:
                    mime_type = part.get('mimeType', '')
                    if mime_type == 'text/html' and 'data' in part['body']:
                        body_html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                    elif mime_type == 'text/plain' and 'data' in part['body']:
                        body_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
                    # Handle nested parts (multipart/alternative)
                    elif mime_type == 'multipart/alternative':
                        for sub_part in part.get('parts', []):
                            sub_mime_type = sub_part.get('mimeType', '')
                            if sub_mime_type == 'text/html' and 'data' in sub_part['body']:
                                body_html = base64.urlsafe_b64decode(sub_part['body']['data']).decode('utf-8', errors='replace')
                            elif sub_mime_type == 'text/plain' and 'data' in sub_part['body']:
                                body_text = base64.urlsafe_b64decode(sub_part['body']['data']).decode('utf-8', errors='replace')
            elif 'body' in payload and 'data' in payload['body']: # For simple, non-multipart emails    
                # This might be plain text or HTML depending on the email
                # For simplicity, assuming it might be plain text if not multipart
                # A more robust parser would check Content-Type header here
                body_text = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')


            emails_data.append({
                "id": msg_info['id'],
                "subject": subject,
                "to": emailto,
                "body_html": body_html or "",
                "body_text": body_text or "",
                "snippet": snippet,
                "labels": labels,
                "from": emailfrom,
                "date_original": emaildate,
                "date_eastern": convert_to_eastern(emaildate)
            })
        
        return emails_data

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def get_labels(service):
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    if not labels:
      print("No labels found.")
      return
    print("Labels:")
    for label in labels:
      print(label["name"])


def convert_to_eastern(date_string):
    """Converts a date string in the format 'Mon, DD Mon YYYY HH:MM:SS -ZZZZ' to Eastern New York time.

    Args:
        date_string: The date string to convert.

    Returns:
        A string representing the date and time in Eastern New York time, 
        or None if the input string is invalid.
    """
    try:
        date_string = date_string[:31]

        # Parse the input string into a datetime object
        dt_object = datetime.datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %z')

        # Convert to Eastern Time
        eastern_tz = pytz.timezone('America/New_York')
        eastern_dt = dt_object.astimezone(eastern_tz)

        # Format the output
        return eastern_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    except ValueError:
        return None

def main():
   messages = get_gmail_messages("after:2025/06/21 AND category:UPDATES",20)
   for message in messages:
      print(f"ID: {message['id']}, Date: {message['date_eastern']}, Labels: {', '.join(message['labels'])}, From : {message['from']}, Subject: {message['subject']}")

if __name__ == "__main__":
  main()
