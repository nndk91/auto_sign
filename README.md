# PDF Batch Signature App

A Streamlit-based web application for automatically signing multiple PDF documents with a digital signature image. The app detects the name "Nguyen Ngoc Dang Khoa" in PDF files and places the signature at a configurable offset position.

## 🆕 Google Sheets Integration

The app supports three modes for signature and record management:

| Mode | Signature Source | Records Storage | Setup Complexity |
|------|-----------------|-----------------|------------------|
| **Local Only** (Default) | `signature.png` file | `sign_records.txt` | None |
| **Public Sheet** | Google Sheets (read-only) | Local file | Low |
| **Service Account** | Google Sheets | Google Sheets | High |

- **Records**: Signing activity with IP address and location
- **Signature**: Read from Google Sheets cell A1 (Signature sheet)
- **Fallback**: Automatically falls back to local files if Sheets is not configured

📖 See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) for detailed setup instructions.

## Features

- **Batch Processing**: Upload and sign multiple PDF files at once
- **Auto-Detection**: Automatically finds "Nguyen Ngoc Dang Khoa" in documents
- **IP Tracking**: Records signing activity with IP address and location
- **Flexible Storage**: Local files, Public Google Sheet, or Service Account
- **Preview Mode**: Visual preview of signature placement before signing
- **ZIP Export**: Download all signed PDFs as a ZIP file
- **Configurable Position**: Adjust signature offset and size via sidebar

## Default Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| Offset X | -90 | Horizontal offset from "Khoa" (negative = left) |
| Offset Y | -80 | Vertical offset from "Khoa" (negative = up) |
| Width | 70 | Signature width in PDF points |
| Height | 70 | Signature height in PDF points |

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository
2. Install required packages:

```bash
pip install -r requirements.txt
```

3. For Google Sheets integration (optional), see options below

4. Ensure you have a signature image (see [Signature Setup](#signature-setup))

### Authentication Setup

The app requires login credentials. These are stored in `.streamlit/secrets.toml`:

**Default credentials:**
- **Username:** `admin`
- **Password:** `pdfsign2024`

**To change credentials**, edit `.streamlit/secrets.toml`:

```toml
[authentication]
username = "your_username"
password = "your_password"
```

> ⚠️ **Security Note:** Keep your `secrets.toml` file secure and do not commit it to public repositories.

## Signature Setup

Choose one of three options:

### Option 1: Local File (Default - No Setup)
Place your signature image as `signature.png` in the app directory.

### Option 2: Public Google Sheet (Read-Only)
1. Create a Google Sheet and publish it to web
2. Create a sheet named `Signature`
3. Put your signature image URL in cell **A1**
4. Edit `google_sheets.py` and set `PUBLIC_SHEET_URL` to your sheet URL

### Option 3: Service Account (Full Access)
1. Set up Google Cloud service account
2. Add credentials to `.streamlit/secrets.toml`
3. Create a `Signature` sheet with image URL in cell A1
4. Share the sheet with your service account email

See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) for detailed instructions.

## Usage

### Run the Streamlit App

```bash
python -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Login

1. Enter your **username** and **password** (default: admin / pdfsign2024)
2. Click **"Log In"**
3. To logout, click the **"🚪 Logout"** button in the sidebar

### Signing PDFs

1. **Upload PDFs**: Drag and drop or select multiple PDF files
2. **Get IP Info** (optional): Click "🌐 Get IP Info" to record location data
3. **Preview** (optional): Select a file and click "👁️ Preview Position" to verify placement
4. **Sign**: Click "🖊️ Sign All PDFs" to process all uploaded files
5. **Download**: Download individual signed PDFs or all as a ZIP file

### Adjusting Signature Position

Use the sidebar to adjust:
- **Offset X**: Move signature left/right relative to "Khoa"
- **Offset Y**: Move signature up/down relative to "Khoa"
- **Width/Height**: Change signature size

Click "👁️ Preview Position" to see the red box indicating signature placement.

## Files

| File | Description |
|------|-------------|
| `app.py` | Streamlit web application |
| `sign_auto.py` | Command-line batch signing script |
| `google_sheets.py` | Google Sheets integration module |
| `signature.png` | Your signature image (local fallback) |
| `sign_records.txt` | Auto-generated signing records (local backup) |
| `requirements.txt` | Python package dependencies |
| `.streamlit/secrets.toml` | Login credentials and Google Sheets configuration |
| `GOOGLE_SHEETS_SETUP.md` | Detailed Google Sheets setup instructions |

## Google Sheets Configuration (Optional)

### Quick Comparison

| Feature | Local Only | Public Sheet | Service Account |
|---------|-----------|--------------|-----------------|
| Setup Time | 0 min | 5 min | 20 min |
| Signature from Sheets | ❌ | ✅ Read-only | ✅ Read/Write |
| Records to Sheets | ❌ | ❌ | ✅ Yes |
| Requires Google Cloud | ❌ | ❌ | ✅ Yes |
| Best For | Testing | Shared signature URL | Production/Team use |

### Option 1: Local Only (Default)
By default, the app uses **local storage**:
- Records saved to `sign_records.txt`
- Signature loaded from `signature.png`
- No Google account or credentials needed

### Option 2: Public Google Sheet
For reading signature URL from a public sheet:
1. Create and publish a Google Sheet to web
2. Add `Signature` sheet with image URL in A1
3. Edit `google_sheets.py`: `PUBLIC_SHEET_URL = "your_sheet_url"`

**Note:** Records are still saved locally. See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) for full instructions.

### Option 3: Service Account (Full Access)
For saving records to Google Sheets:
1. Create service account in [Google Cloud Console](https://console.cloud.google.com/)
2. Download JSON credentials
3. Add credentials to `.streamlit/secrets.toml`
4. Share sheet with service account email

See [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md) for step-by-step instructions.

## Command-Line Batch Signing

For automated batch processing without the GUI, use `sign_auto.py`:

```bash
python sign_auto.py
```

This will:
- Sign all PDFs matching `PO *.pdf` pattern
- Use default offsets (X=-90, Y=-80, Size=70x70)
- Save records to `sign_records.txt`
- Display IP location information

## Record Format

Records are saved as JSON in `sign_records.txt`:

```json
[
  {
    "timestamp": "2026-04-29T10:30:00",
    "input_file": "PO 28042026-01 TAEJIN.pdf",
    "output_file": "PO 28042026-01 TAEJIN_signed.pdf",
    "ip_info": {
      "public_ip": "203.210.226.113",
      "local_ip": "192.168.137.1",
      "city": "unknown",
      "region": "unknown",
      "country": "unknown"
    },
    "position": {"x": 341.6, "y": 446.2},
    "detection_method": "auto"
  }
]
```

When using Service Account, records are also saved to the Google Sheet "data" tab with columns:
- Input File | Output File | Public IP | Local IP | City | Region | Country | Position X | Position Y | Detection Method

## Troubleshooting

### Name Not Found
If the app cannot find "Nguyen Ngoc Dang Khoa":
1. Check the PDF is text-based (not scanned image)
2. Use "👁️ Preview Position" to verify
3. The app will use default position (X=340, Y=440) as fallback

### Signature Position Wrong
1. Use Preview mode with red box to see placement
2. Adjust Offset X and Y values
3. Negative X moves left, negative Y moves up

### Google Sheets Issues

**"Service account info was not in the expected format"**
- Check `.streamlit/secrets.toml` has all required fields
- Ensure private key is properly formatted with triple quotes

**"Sheets connected but no signature URL"**
- Verify cell A1 in Signature sheet contains a valid URL
- URL must start with `http://` or `https://`

**"Public sheet error"**
- Ensure sheet is published to web (File → Share → Publish to web)
- Check `PUBLIC_SHEET_URL` in `google_sheets.py` is correct

### Dependencies Issues
If you encounter import errors:
```bash
pip install --upgrade -r requirements.txt
```

## Requirements

- Python 3.8+
- PyMuPDF (fitz) - PDF manipulation
- pdfplumber - PDF text extraction
- Streamlit - Web interface
- Pillow (PIL) - Image processing
- Requests - IP geolocation
- gspread - Google Sheets API (optional)
- google-auth - Google authentication (optional)

## License

This project is for internal use.

## Author

Created for PDF signature automation.
