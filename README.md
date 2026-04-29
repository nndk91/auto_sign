# PDF Batch Signature App

A Streamlit-based web application for automatically signing multiple PDF documents with a digital signature image. The app detects the name "Nguyen Ngoc Dang Khoa" in PDF files and places the signature at a configurable offset position.

## Features

- **Batch Processing**: Upload and sign multiple PDF files at once
- **Auto-Detection**: Automatically finds "Nguyen Ngoc Dang Khoa" in documents
- **IP Tracking**: Records signing activity with IP address and location
- **Local Record Storage**: Automatically saves signing records to `sign_records.txt`
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

3. Ensure you have a signature image file named `signature.png` in the same directory

## Usage

### Run the Streamlit App

```bash
python -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

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
| `signature.png` | Your signature image (required) |
| `sign_records.txt` | Auto-generated signing records (JSON format) |
| `requirements.txt` | Python package dependencies |

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

## License

This project is for internal use.

## Author

Created for PDF signature automation.
