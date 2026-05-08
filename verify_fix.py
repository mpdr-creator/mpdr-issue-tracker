
import gspread
from google.oauth2.service_account import Credentials
import toml
import os
import sys

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

def safe_get_all_records(ws):
    """Copied from app.py for local verification."""
    all_values = ws.get_all_values()
    if not all_values:
        return []
    headers = [h.strip() for h in all_values[0]]
    valid_header_indices = [i for i, h in enumerate(headers) if h]
    clean_headers = [headers[i] for i in valid_header_indices]
    
    data = []
    for row in all_values[1:]:
        if any(row):
            record = {}
            for i, h_name in enumerate(clean_headers):
                idx = valid_header_indices[i]
                record[h_name] = row[idx] if idx < len(row) else ""
            data.append(record)
    return data

def verify():
    try:
        client = get_client()
        ss = client.open("MPDR Issue Tracker")
        ws = ss.worksheet("tickets")
        
        print("Attempting to read 'tickets' worksheet using safe_get_all_records...")
        records = safe_get_all_records(ws)
        print(f"Success! Read {len(records)} records.")
        if records:
            print(f"First record sample: {records[0]}")
        
    except Exception as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
