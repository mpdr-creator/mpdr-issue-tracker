
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import toml
import os

# Mock streamlit secrets for local run
def load_secrets():
    secrets_path = "c:/Users/Hi/Desktop/IMS/secrets.toml"
    if os.path.exists(secrets_path):
        return toml.load(secrets_path)
    return {}

secrets = load_secrets()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]

def get_client():
    creds = Credentials.from_service_account_info(dict(secrets["gcp_service_account"]), scopes=SCOPES)
    return gspread.authorize(creds)

def diag():
    try:
        client = get_client()
        ss = client.open("MPDR Issue Tracker")
        print(f"Spreadsheet found: {ss.title}")
        
        try:
            ws = ss.worksheet("tickets")
            print(f"Worksheet 'tickets' found.")
            
            rows = ws.get_all_values()
            if not rows:
                print("Error: 'tickets' worksheet is completely empty (no headers).")
            else:
                headers = rows[0]
                print(f"Headers: {headers}")
                if len(headers) != len(set(headers)):
                    duplicates = set([x for x in headers if headers.count(x) > 1])
                    print(f"Error: Duplicate headers found: {duplicates}")
                
                if len(rows) == 1:
                    print("Note: 'tickets' worksheet only has headers, no data records.")
                else:
                    print(f"Data records count: {len(rows) - 1}")
                    
        except gspread.WorksheetNotFound:
            print("Error: Worksheet 'tickets' not found.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    diag()
