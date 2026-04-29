# Google Sheets Integration Setup Guide

This guide explains how to set up Google Sheets integration for the PDF Signature App.

## Overview

The app supports three modes:
1. **Local Only** (default) - Uses local `signature.png` and `sign_records.txt`
2. **Public Sheet** (read-only) - Reads signature URL from a public Google Sheet
3. **Service Account** (full access) - Read/write to private Google Sheets

## Option 1: Local Storage Only (Default)

If you don't configure Google Sheets, the app will:
- Use local `signature.png` for signing
- Save records to local `sign_records.txt`

No setup required!

## Option 2: Public Google Sheet (Read-Only)

This option allows you to read the signature image URL from a **public** Google Sheet without authentication. Records are still saved locally.

### Setup Steps

#### 1. Create and Publish Your Google Sheet

1. Create a new Google Sheet
2. Create a sheet named `Signature` (or use default "Sheet1")
3. In cell **A1**, paste the URL to your signature image
   - Example: `https://i.imgur.com/your-signature.png`
4. Go to **File → Share → Publish to web**
5. Click **Publish**

#### 2. Get Your Sheet URL or ID

Copy the sheet URL. It will look like:
```
https://docs.google.com/spreadsheets/d/1B7tm0A6ftusbGwqFlHn5d8tZ_FM0dPimLn8kHdDDE7U/edit
```

Or extract just the ID:
```
1B7tm0A6ftusbGwqFlHn5d8tZ_FM0dPimLn8kHdDDE7U
```

#### 3. Update `google_sheets.py`

Edit the `PUBLIC_SHEET_URL` variable in `google_sheets.py`:

```python
# Option 1: Public Sheet (read-only, no auth needed)
# Set this to your public Google Sheet URL or ID
PUBLIC_SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit"
```

Or use just the ID:
```python
PUBLIC_SHEET_URL = "YOUR_SHEET_ID_HERE"
```

#### 4. Test the Connection

Run the app and check the sidebar. It should show:
- ✅ **Connected (Public Sheet)**

**Note:** Records will be saved locally, not to Google Sheets.

## Option 3: Service Account (Full Read/Write Access)

To save records to Google Sheets and have full read/write access, you need to set up a **service account**.

### Setup Steps

#### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Also enable "Google Drive API" (needed for accessing sheets)

#### 2. Create Service Account

1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Enter a name (e.g., "pdf-signature-app")
4. Click "Create and Continue"
5. For Role, select "Editor"
6. Click "Done"

#### 3. Generate and Download Credentials

1. Click on your newly created service account
2. Go to the "Keys" tab
3. Click "Add Key" → "Create New Key"
4. Select "JSON" format
5. Click "Create"
6. The JSON file will download automatically (e.g., `project-name-123456.json`)

#### 4. Configure Secrets in `.streamlit/secrets.toml`

Open the downloaded JSON file and copy the values to `.streamlit/secrets.toml`:

```toml
# Streamlit Secrets Configuration

[authentication]
username = "admin"
password = "pdfsign2024"

[connections.gsheets]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = """
-----BEGIN RSA PRIVATE KEY-----
YOUR_PRIVATE_KEY_LINE_1
YOUR_PRIVATE_KEY_LINE_2
YOUR_PRIVATE_KEY_LINE_3
... (many more lines - about 20-30 total)
YOUR_PRIVATE_KEY_LAST_LINE
-----END RSA PRIVATE KEY-----
"""
client_email = "YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/YOUR_SERVICE_ACCOUNT%40YOUR_PROJECT.iam.gserviceaccount.com"
```

**⚠️ IMPORTANT - Private Key Format:**
1. Use **triple quotes** `"""` to wrap the private key
2. The key must have **actual newlines**, not `\n` text
3. Copy the private_key from the JSON and ensure each line is on a new line
4. The key should span **20-30 lines** in the TOML file

#### 5. Share the Google Sheet

1. Open the Google Sheet: [Link](https://docs.google.com/spreadsheets/d/1B7tm0A6ftusbGwqFlHn5d8tZ_FM0dPimLn8kHdDDE7U/edit?usp=sharing)
2. Click **"Share"** button (top right)
3. Add the **service account email** (from `client_email` in your secrets.toml)
   - Example: `pdf-signature-app@your-project.iam.gserviceaccount.com`
4. Set permission to **"Editor"**
5. Click **"Share"**

#### 6. Set Up Sheet Structure

**Data Sheet ("data")**
The app will auto-create this sheet with headers:
| Input File | Output File | Public IP | Local IP | City | Region | Country | Position X | Position Y | Detection Method |

**Signature Sheet ("Signature")**
1. Create a new sheet named exactly: `Signature`
2. In cell **A1**, paste the URL to your signature image
   - Example: `https://i.imgur.com/your-signature.png`

#### 7. Test the Integration

1. Run the app:
   ```bash
   python -m streamlit run app.py
   ```
2. Check the sidebar - it should show "✅ Connected" under "📊 Google Sheets"
3. Sign a PDF
4. Check the Google Sheet - your record should appear in the "data" sheet

## Troubleshooting

### Public Sheet Issues

#### "Public sheet error" or unable to read from public sheet
- Make sure the sheet is **published to web** (File → Share → Publish to web)
- Verify the sheet ID or URL in `google_sheets.py` is correct
- Check that the sheet name (default: "Signature") exists
- Ensure cell A1 contains a valid image URL

#### "Sheet not found" when using public sheet
- The app looks for a sheet named "Signature" by default
- If your sheet uses a different name, update `SIGNATURE_SHEET_NAME` in `google_sheets.py`
- Or use the default "Sheet1" by leaving it as is

### Service Account Issues

#### "Unable to connect to Google Sheets"
- Verify the Google Sheets API is enabled in Google Cloud Console
- Check that all required fields are in `secrets.toml`: `client_email`, `token_uri`, `private_key`
- Ensure the private key format is correct (actual newlines, not `\n`)

#### "Signature not loading from Sheets"
- Verify the sheet is named exactly "Signature" (case-sensitive)
- Check that cell A1 contains a valid, publicly accessible image URL
- The image URL must start with `http://` or `https://`

#### "Permission denied"
- The service account email must be added as an editor to the Google Sheet
- Double-check the email address matches `client_email` in secrets

#### "Service account info was not in the expected format"
- Make sure all required fields are present in `secrets.toml`
- Required: `type`, `project_id`, `private_key_id`, `private_key`, `client_email`, `client_id`, `token_uri`

### Private key format issues

Make sure the private key in `secrets.toml` is formatted correctly:

```toml
private_key = """
-----BEGIN RSA PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQE... (line 1)
... (line 2)
... (many more lines)
... (last line)
-----END RSA PRIVATE KEY-----
"""
```

## Using Without Google Sheets

If you prefer not to use Google Sheets at all:
1. Don't add `[connections.gsheets]` to `secrets.toml`
2. Set `PUBLIC_SHEET_URL = ""` in `google_sheets.py`
3. The app will automatically use local storage
4. Records save to `sign_records.txt`
5. Signature reads from `signature.png`

## Summary: Which Option Should I Choose?

| Option | Setup Complexity | Signature Source | Records Storage | Best For |
|--------|-----------------|------------------|-----------------|----------|
| **Local Only** | None | `signature.png` file | `sign_records.txt` | Single user, simple setup |
| **Public Sheet** | Low | Google Sheets (read-only) | `sign_records.txt` | Shared signature, no auth needed |
| **Service Account** | High | Google Sheets | Google Sheets | Multi-user, cloud storage |

**Recommendation:**
- Start with **Local Only** for testing
- Use **Public Sheet** if you want a shared signature URL without complex setup
- Use **Service Account** only if you need full cloud integration

## Security Notes

⚠️ **Important:**
- Never commit `.streamlit/secrets.toml` to public repositories if it contains credentials
- Add `.streamlit/secrets.toml` to your `.gitignore` file
- Keep your service account credentials secure
