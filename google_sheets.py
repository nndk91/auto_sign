"""
Google Sheets integration for PDF Signature App
Supports both public sheets (read-only) and service account (read/write)
"""
import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import requests
import csv
import io

# Google Sheets configuration
# Option 1: Public Sheet (read-only, no auth needed)
# Set this to your public Google Sheet URL or ID
PUBLIC_SHEET_URL = "https://docs.google.com/spreadsheets/d/1B7tm0A6ftusbGwqFlHn5d8tZ_FM0dPimLn8kHdDDE7U/edit"

# Option 2: Private Sheet with Service Account (for full read/write)
SPREADSHEET_ID = "1B7tm0A6ftusbGwqFlHn5d8tZ_FM0dPimLn8kHdDDE7U"
DATA_SHEET_NAME = "data"
SIGNATURE_SHEET_NAME = "Signature"
SIGNATURE_CELL = "A1"

# Parse public sheet ID from various URL formats
def extract_sheet_id(url_or_id):
    """Extract sheet ID from URL or return as-is if already an ID."""
    if not url_or_id:
        return None
    url_or_id = url_or_id.strip()
    # If it's already just an ID (no slashes), return it
    if '/' not in url_or_id and len(url_or_id) == 44:
        return url_or_id
    # Extract from URL formats
    if '/d/' in url_or_id:
        parts = url_or_id.split('/d/')
        if len(parts) > 1:
            sheet_id = parts[1].split('/')[0]
            return sheet_id
    if 'spreadsheets/d/' in url_or_id:
        parts = url_or_id.split('spreadsheets/d/')
        if len(parts) > 1:
            sheet_id = parts[1].split('/')[0]
            return sheet_id
    return None


def get_google_client():
    """Get authenticated Google Sheets client from secrets."""
    try:
        # Check if credentials are configured
        if "connections" not in st.secrets:
            return None, "No connections configured in secrets"
        
        if "gsheets" not in st.secrets["connections"]:
            return None, "No gsheets connection configured"
        
        credentials_info = dict(st.secrets["connections"]["gsheets"])
        
        # Check required fields
        required_fields = ["client_email", "token_uri", "private_key"]
        missing_fields = [f for f in required_fields if f not in credentials_info or not credentials_info[f]]
        
        if missing_fields:
            return None, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Import here to avoid errors if not installed
        from google.oauth2.service_account import Credentials
        import gspread
        
        # Fix private key formatting
        if "private_key" in credentials_info:
            private_key = credentials_info["private_key"]
            private_key = private_key.replace("\\n", "\n")
            private_key = private_key.strip()
            credentials_info["private_key"] = private_key
        
        # Create credentials
        creds = Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
        # Create client
        client = gspread.authorize(creds)
        return client, None
        
    except ImportError as e:
        return None, f"Missing required package: {e}"
    except Exception as e:
        return None, str(e)


def read_public_sheet_csv(sheet_id, sheet_name="Sheet1", cell=None):
    """
    Read data from a public Google Sheet using CSV export.
    Returns the value at specified cell or all data if no cell specified.
    """
    try:
        # Google Sheets CSV export URL
        # Format: https://docs.google.com/spreadsheets/d/{ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        
        response = requests.get(csv_url, timeout=30)
        
        if response.status_code != 200:
            return None, f"Failed to fetch sheet: HTTP {response.status_code}"
        
        # Parse CSV
        csv_content = response.content.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        
        if not rows:
            return None, "Sheet is empty"
        
        # If cell is specified (e.g., "A1"), return that specific value
        if cell:
            # Parse cell reference (e.g., "A1" -> row 0, col 0)
            import re
            match = re.match(r'([A-Z]+)(\d+)', cell.upper())
            if match:
                col_str, row_str = match.groups()
                row_idx = int(row_str) - 1  # 0-based index
                
                # Convert column letters to index (A=0, B=1, etc.)
                col_idx = 0
                for char in col_str:
                    col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
                col_idx -= 1
                
                if row_idx < len(rows) and col_idx < len(rows[row_idx]):
                    return rows[row_idx][col_idx], None
                else:
                    return None, f"Cell {cell} is out of range"
            else:
                return None, f"Invalid cell format: {cell}"
        
        # Return all data
        return rows, None
        
    except Exception as e:
        return None, str(e)


def save_record_to_sheets(record):
    """Save a signing record to Google Sheets (requires service account)."""
    client, error = get_google_client()
    if error:
        return False, f"Service account not configured: {error}"
    
    try:
        import gspread
        
        # Open spreadsheet
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        
        # Get or create data worksheet
        try:
            worksheet = spreadsheet.worksheet(DATA_SHEET_NAME)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=DATA_SHEET_NAME, rows=1000, cols=12)
            headers = [
                "Timestamp", "Input File", "Output File", "Public IP", "Local IP",
                "City", "Region", "Country", "Position X", "Position Y", "Detection Method"
            ]
            worksheet.append_row(headers)
        
        # Prepare row data
        ip_info = record.get("ip_info", {})
        position = record.get("position", {})
        
        row = [
            record.get("timestamp", ""),
            record.get("input_file", ""),
            record.get("output_file", ""),
            ip_info.get("public_ip", ""),
            ip_info.get("local_ip", ""),
            ip_info.get("city", ""),
            ip_info.get("region", ""),
            ip_info.get("country", ""),
            position.get("x", ""),
            position.get("y", ""),
            record.get("detection_method", "")
        ]
        
        worksheet.append_row(row)
        return True, None
        
    except Exception as e:
        return False, str(e)


def is_valid_url(url):
    """Check if a string is a valid URL (starts with http:// or https://)."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return url.startswith('http://') or url.startswith('https://')


def get_signature_from_sheets():
    """Get signature image URL from Google Sheets (service account or public)."""
    # First try service account
    client, error = get_google_client()
    
    if client:
        # Service account method
        try:
            import gspread
            
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            
            try:
                worksheet = spreadsheet.worksheet(SIGNATURE_SHEET_NAME)
                signature_url = worksheet.acell(SIGNATURE_CELL).value
                if is_valid_url(signature_url):
                    return signature_url, None
                else:
                    return None, f"Invalid URL in {SIGNATURE_CELL}: {signature_url}"
            except gspread.WorksheetNotFound:
                return None, f"Sheet '{SIGNATURE_SHEET_NAME}' not found"
                
        except Exception as e:
            return None, str(e)
    
    # Try public sheet method
    public_sheet_id = extract_sheet_id(PUBLIC_SHEET_URL)
    if public_sheet_id:
        sig_url, error = read_public_sheet_csv(public_sheet_id, SIGNATURE_SHEET_NAME, SIGNATURE_CELL)
        if sig_url and is_valid_url(sig_url):
            return sig_url, None
        # Try with default "Sheet1" if Signature sheet not found
        sig_url, error = read_public_sheet_csv(public_sheet_id, "Sheet1", SIGNATURE_CELL)
        if sig_url and is_valid_url(sig_url):
            return sig_url, None
        if sig_url:
            return None, f"Invalid URL in {SIGNATURE_CELL}: '{sig_url}' (must start with http:// or https://)"
        return None, f"Public sheet error: {error}"
    
    return None, f"Service account: {error}. Public sheet: URL not configured."


def download_signature_image(url, output_path="signature.png"):
    """Download signature image from URL."""
    import requests
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True, None
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def load_records_from_sheets():
    """Load all records from Google Sheets (service account only)."""
    client, error = get_google_client()
    if error:
        return [], f"Service account not configured: {error}"
    
    try:
        import gspread
        
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        
        try:
            worksheet = spreadsheet.worksheet(DATA_SHEET_NAME)
            records = worksheet.get_all_records()
            return records, None
        except gspread.WorksheetNotFound:
            return [], f"Sheet '{DATA_SHEET_NAME}' not found"
            
    except Exception as e:
        return [], str(e)


def get_sheets_status():
    """Get Google Sheets connection status."""
    # Check service account
    client, error = get_google_client()
    if client:
        return "connected_service_account", None
    
    # Check public sheet
    public_sheet_id = extract_sheet_id(PUBLIC_SHEET_URL)
    if public_sheet_id:
        # Try to read from it
        test_data, test_error = read_public_sheet_csv(public_sheet_id, SIGNATURE_SHEET_NAME, SIGNATURE_CELL)
        if test_data:
            return "connected_public", None
        # Try Sheet1
        test_data, test_error = read_public_sheet_csv(public_sheet_id, "Sheet1", SIGNATURE_CELL)
        if test_data:
            return "connected_public", None
        return "public_sheet_error", test_error
    
    return "not_configured", f"Service account: {error}. No public sheet configured."
