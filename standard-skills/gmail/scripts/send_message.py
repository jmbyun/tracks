#!/usr/bin/env python3
import sys
import argparse
import base64
from email.message import EmailMessage
from auth import make_gmail_request

def send_message(to, subject, body, cc=None, bcc=None):
    try:
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject
        
        if cc:
            message['Cc'] = cc
        if bcc:
            message['Bcc'] = bcc
            
        # encode the email message into base64 url-safe string
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        create_message = {
            'raw': encoded_message
        }
        
        sent_message = make_gmail_request("messages/send", method="POST", data=create_message)
        
        print(f"Successfully sent message to '{to}' with ID: {sent_message['id']}")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send an email using Gmail.')
    parser.add_argument('--to', type=str, required=True, help='Recipient email address')
    parser.add_argument('--subject', type=str, required=True, help='Email subject line')
    parser.add_argument('--body', type=str, required=True, help='Email body text content')
    parser.add_argument('--cc', type=str, help='Cc recipients (comma-separated)')
    parser.add_argument('--bcc', type=str, help='Bcc recipients (comma-separated)')
    args = parser.parse_args()
    
    send_message(args.to, args.subject, args.body, args.cc, args.bcc)
