import streamlit as st
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import json
import socket
import requests
from datetime import datetime
import base64
import zipfile

# Import Google Sheets module
try:
    from google_sheets import (
        save_record_to_sheets, 
        get_signature_from_sheets, 
        load_records_from_sheets,
        download_signature_image,
        get_sheets_status,
        DATA_SHEET_NAME,
        SIGNATURE_SHEET_NAME
    )
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError as e:
    GOOGLE_SHEETS_AVAILABLE = False

st.set_page_config(page_title="PDF Batch Signature App", layout="wide")

# ==================== AUTHENTICATION ====================
def check_password():
    """Returns True if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] == st.secrets["authentication"]["username"] and \
           st.session_state["password"] == st.secrets["authentication"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🔒 PDF Signature App</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Please log in to continue</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            submit = st.form_submit_button("Log In", use_container_width=True)
            
            if submit:
                password_entered()
                if not st.session_state["password_correct"]:
                    st.error("😕 User not known or password incorrect")
        return False
    
    elif not st.session_state["password_correct"]:
        st.markdown("<h1 style='text-align: center;'>🔒 PDF Signature App</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Please log in to continue</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            submit = st.form_submit_button("Log In", use_container_width=True)
            
            if submit:
                password_entered()
                if not st.session_state["password_correct"]:
                    st.error("😕 User not known or password incorrect")
        return False
    
    else:
        return True


if not check_password():
    st.stop()
# ==================== END AUTHENTICATION ====================

# Default configuration
DEFAULT_CONFIG = {
    "offset_x": -90,
    "offset_y": -80,
    "sig_width": 70,
    "sig_height": 70,
    "signature_path": "signature.png",
    "record_file": "sign_records.txt"
}

st.title("📄 PDF Batch Signature App")
st.markdown("Upload multiple PDF files to sign them automatically")

# Quick Usage Guide
with st.expander("📖 Hướng Dẫn Sử Dụng / Usage Guide", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🇻🇳 Tiếng Việt:**
        
        1. **Tải lên PDF** - Chọn một hoặc nhiều file
        2. **Xem trước** - Kiểm tra vị trí chữ ký
        3. **Ký file** - Nhấn "Sign All PDFs"
        4. **Tải xuống** - Lấy file đã ký
        
        *Điều chỉnh Offset X/Y trong sidebar để thay đổi vị trí chữ ký*
        """)
    with col2:
        st.markdown("""
        **🇬🇧 English:**
        
        1. **Upload PDFs** - Select one or more files
        2. **Preview** - Check signature position
        3. **Sign** - Click "Sign All PDFs"
        4. **Download** - Get signed files
        
        *Adjust Offset X/Y in sidebar to change signature position*
        """)


@st.cache_data(ttl=300)
def get_signature_from_source():
    """Get signature from Google Sheets or fallback to local file."""
    # Try Google Sheets first if available
    if GOOGLE_SHEETS_AVAILABLE:
        status, error = get_sheets_status()
        if status in ["connected_service_account", "connected_public"]:
            sig_url, error = get_signature_from_sheets()
            if sig_url:
                success, dl_error = download_signature_image(sig_url, DEFAULT_CONFIG["signature_path"])
                if success:
                    source_type = "Service Account" if status == "connected_service_account" else "Public Sheet"
                    return DEFAULT_CONFIG["signature_path"], f"Loaded from Google Sheets ({source_type})"
                else:
                    return DEFAULT_CONFIG["signature_path"], f"Sheets connected but download failed: {dl_error}"
            else:
                return DEFAULT_CONFIG["signature_path"], f"Sheets connected but no signature URL: {error}"
    
    # Fallback to local file
    if os.path.exists(DEFAULT_CONFIG["signature_path"]):
        return DEFAULT_CONFIG["signature_path"], "Using local signature.png (Google Sheets not configured)"
    else:
        return None, "No signature found! Please add signature.png or configure Google Sheets."


def get_ip_info():
    """Get IP address and location information."""
    try:
        ip_response = requests.get("https://api.ipify.org?format=json", timeout=5)
        public_ip = ip_response.json().get("ip", "unknown")
        
        loc_response = requests.get(f"https://ipapi.co/{public_ip}/json/", timeout=5)
        location_data = loc_response.json()
        
        return {
            "public_ip": public_ip,
            "city": location_data.get("city", "unknown"),
            "region": location_data.get("region", "unknown"),
            "country": location_data.get("country_name", "unknown"),
            "org": location_data.get("org", "unknown"),
            "local_ip": socket.gethostbyname(socket.gethostname())
        }
    except Exception as e:
        return {
            "public_ip": "unknown",
            "city": "unknown",
            "region": "unknown",
            "country": "unknown",
            "org": "unknown",
            "local_ip": socket.gethostbyname(socket.gethostname()),
            "error": str(e)
        }


def find_name_position(pdf_bytes):
    """Find the position of 'Nguyen Ngoc Dang Khoa' in the PDF."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words()
                
                for i, word in enumerate(words):
                    text = word.get("text", "")
                    if "Nguyen" in text:
                        for j in range(i + 1, min(i + 5, len(words))):
                            if "Khoa" in words[j].get("text", ""):
                                khoa_word = words[j]
                                return {
                                    "page_num": page_num,
                                    "khoa_x": khoa_word["x1"],
                                    "khoa_y": khoa_word["top"],
                                    "found": True
                                }
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    
    return {"found": False}


def sign_pdf(input_bytes, signature_path, position_info, config):
    """Sign a single PDF file."""
    try:
        if position_info["found"]:
            sig_x = position_info["khoa_x"] + config["offset_x"]
            sig_y = position_info["khoa_y"] + config["offset_y"]
            detection_status = "auto"
        else:
            sig_x = 340
            sig_y = 440
            detection_status = "manual_fallback"
        
        pdf_document = fitz.open(stream=input_bytes, filetype="pdf")
        page = pdf_document[0]
        
        rect = fitz.Rect(
            sig_x, 
            sig_y, 
            sig_x + config["sig_width"], 
            sig_y + config["sig_height"]
        )
        
        page.insert_image(rect, filename=signature_path)
        
        output_bytes = io.BytesIO()
        pdf_document.save(output_bytes)
        pdf_document.close()
        output_bytes.seek(0)
        
        return {
            "success": True,
            "detection": detection_status,
            "position": {"x": sig_x, "y": sig_y},
            "output_bytes": output_bytes
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def save_record(record):
    """Save a record to Google Sheets and local file."""
    sheets_saved = False
    
    # Try to save to Google Sheets if available (service account only)
    if GOOGLE_SHEETS_AVAILABLE:
        status, _ = get_sheets_status()
        if status == "connected_service_account":
            success, error = save_record_to_sheets(record)
            if success:
                sheets_saved = True
            else:
                st.warning(f"Google Sheets save failed: {error}")
    
    # Always save to local file as backup
    records = load_records_from_file()
    records.append(record)
    save_records_to_file(records)
    
    # Update session state
    if "sign_records" not in st.session_state:
        st.session_state.sign_records = []
    st.session_state.sign_records.append(record)
    
    return sheets_saved


def load_records_from_file():
    """Load existing records from local file (backup)."""
    record_file = DEFAULT_CONFIG["record_file"]
    if os.path.exists(record_file):
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_records_to_file(records):
    """Save records to local file (backup)."""
    record_file = DEFAULT_CONFIG["record_file"]
    try:
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Failed to save local backup: {e}")


def load_all_records():
    """Load records from Google Sheets or fallback to local file."""
    if GOOGLE_SHEETS_AVAILABLE:
        status, _ = get_sheets_status()
        if status == "connected_service_account":
            records, error = load_records_from_sheets()
            if error:
                st.warning(f"Google Sheets read failed: {error}")
                return load_records_from_file()
            return records
    return load_records_from_file()


def get_pdf_preview(pdf_bytes, zoom=1.5):
    """Convert PDF page to image for preview."""
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = pdf_document[0]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pdf_document.close()
        return img_data
    except:
        return None


# Initialize session state
if "signed_files" not in st.session_state:
    st.session_state.signed_files = {}
if "ip_info" not in st.session_state:
    st.session_state.ip_info = None

# Load signature
sig_path, sig_status = get_signature_from_source()

# Sidebar
with st.sidebar:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["password_correct"] = False
        st.rerun()
    
    st.markdown("---")
    st.header("⚙️ Configuration")
    
    # Show signature source status
    st.caption(f"Signature: {sig_status}")
    
    st.subheader("Signature Position")
    offset_x = st.number_input("Offset X", value=DEFAULT_CONFIG["offset_x"], step=5)
    offset_y = st.number_input("Offset Y", value=DEFAULT_CONFIG["offset_y"], step=5)
    sig_width = st.number_input("Width", value=DEFAULT_CONFIG["sig_width"], step=5)
    sig_height = st.number_input("Height", value=DEFAULT_CONFIG["sig_height"], step=5)
    
    st.subheader("Signature Preview")
    if sig_path and os.path.exists(sig_path):
        st.image(sig_path, width=150)
    else:
        st.error("Signature not found!")
    
    # Google Sheets status
    st.markdown("---")
    st.subheader("📊 Google Sheets")
    
    if GOOGLE_SHEETS_AVAILABLE:
        status, error = get_sheets_status()
        if status == "connected_service_account":
            st.success("✅ Connected (Service Account)")
            st.caption(f"Data: {DATA_SHEET_NAME}")
            st.caption(f"Signature: {SIGNATURE_SHEET_NAME}")
        elif status == "connected_public":
            st.success("✅ Connected (Public Sheet)")
            st.caption(f"Reading from: {SIGNATURE_SHEET_NAME}")
            st.caption("Records saved locally")
        elif status == "public_sheet_error":
            st.warning("⚠️ Public sheet error")
            st.caption(f"Error: {error}")
        else:
            st.info("ℹ️ Not configured")
            st.caption("Records save locally only")
            with st.expander("How to enable Google Sheets"):
                st.markdown(
                    "**Option 1: Public Sheet (Read-only)**\n\n"
                    "Edit `google_sheets.py` and set:\n\n"
                    '```python\n'
                    'PUBLIC_SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID"\n'
                    '```\n\n'
                    "Make sure the sheet is published to web.\n\n"
                    "**Option 2: Service Account (Full access)**\n\n"
                    "1. Enable Google Sheets API in [Google Cloud Console](https://console.cloud.google.com/)\n"
                    "2. Create a service account and download JSON key\n"
                    "3. Add credentials to `.streamlit/secrets.toml`\n"
                    "4. Share the sheet with the `client_email`"
                )
    else:
        st.error("❌ Not available")
        st.caption("Install: pip install gspread google-auth")
    
    # IP Info
    if st.button("🌐 Get IP Info"):
        with st.spinner("Getting IP info..."):
            st.session_state.ip_info = get_ip_info()
    
    if st.session_state.ip_info:
        st.subheader("🌐 IP Information")
        st.write(f"Public IP: {st.session_state.ip_info['public_ip']}")
        st.write(f"Local IP: {st.session_state.ip_info['local_ip']}")
        st.write(f"Location: {st.session_state.ip_info['city']}, {st.session_state.ip_info['region']}")
    
    # Usage Guide in Vietnamese
    st.markdown("---")
    st.subheader("📖 Hướng Dẫn Sử Dụng")
    with st.expander("Xem hướng dẫn"):
        st.markdown("""
        **Các bước ký PDF:**
        
        1. **Tải lên file PDF** - Kéo thả hoặc chọn nhiều file PDF cùng lúc
        2. **Lấy thông tin IP** (tùy chọn) - Nhấn "🌐 Get IP Info" để ghi lại vị trí
        3. **Xem trước vị trí** (tùy chọn) - Chọn file và nhấn "👁️ Preview Position"
        4. **Ký tất cả** - Nhấn "🖊️ Sign All PDFs" để xử lý
        5. **Tải xuống** - Tải từng file hoặc tất cả dưới dạng ZIP
        
        **Điều chỉnh vị trí chữ ký:**
        - **Offset X**: Dịch chuyển ngang (âm = trái, dương = phải)
        - **Offset Y**: Dịch chuyển dọc (âm = lên, dương = xuống)
        - **Width/Height**: Thay đổi kích thước chữ ký
        
        **Lưu ý:**
        - App tự động tìm chữ "Nguyen Ngoc Dang Khoa" trong PDF
        - Nếu không tìm thấy, sẽ dùng vị trí mặc định
        - Chữ ký có thể từ file local (`signature.png`) hoặc Google Sheets
        """)

# Main content
st.subheader("📤 Upload PDF Files")
uploaded_files = st.file_uploader(
    "Choose PDF files", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📎 {len(uploaded_files)} file(s) selected")
    
    with st.expander("View selected files"):
        for file in uploaded_files:
            st.write(f"- {file.name} ({len(file.getvalue())//1024} KB)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        preview_file = st.selectbox(
            "Select file to preview",
            [f.name for f in uploaded_files],
            key="preview_select"
        )
        
        if st.button("👁️ Preview Position", use_container_width=True):
            selected_file = next(f for f in uploaded_files if f.name == preview_file)
            file_bytes = selected_file.getvalue()
            
            position_info = find_name_position(file_bytes)
            
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            page = pdf_document[0]
            
            if position_info["found"]:
                sig_x = position_info["khoa_x"] + offset_x
                sig_y = position_info["khoa_y"] + offset_y
                khoa_x, khoa_y = position_info["khoa_x"], position_info["khoa_y"]
                
                rect = fitz.Rect(sig_x, sig_y, sig_x + sig_width, sig_y + sig_height)
                page.draw_rect(rect, color=(1, 0, 0), width=2)
                page.insert_text((sig_x, sig_y - 5), "SIGNATURE", fontsize=8, color=(1, 0, 0))
                
                page.draw_line(fitz.Point(khoa_x-5, khoa_y), fitz.Point(khoa_x+5, khoa_y), color=(0, 0, 1), width=1)
                page.draw_line(fitz.Point(khoa_x, khoa_y-5), fitz.Point(khoa_x, khoa_y+5), color=(0, 0, 1), width=1)
                
                st.info(f"Found 'Khoa' at X={khoa_x:.1f}, Y={khoa_y:.1f}")
                st.info(f"Signature will be at X={sig_x:.1f}, Y={sig_y:.1f}")
            else:
                st.warning("Name not found - will use default position")
                sig_x, sig_y = 340, 440
                rect = fitz.Rect(sig_x, sig_y, sig_x + sig_width, sig_y + sig_height)
                page.draw_rect(rect, color=(1, 0, 0), width=2)
            
            preview_bytes = io.BytesIO()
            pdf_document.save(preview_bytes)
            pdf_document.close()
            
            img_data = get_pdf_preview(preview_bytes.getvalue())
            if img_data:
                st.image(img_data, caption="Preview: Red box = signature position", use_container_width=True)
    
    with col2:
        if st.button("🖊️ Sign All PDFs", type="primary", use_container_width=True):
            if not sig_path or not os.path.exists(sig_path):
                st.error("❌ Signature image not found! Please check Google Sheets or add signature.png")
                st.stop()
            
            if not st.session_state.ip_info:
                with st.spinner("Getting IP information..."):
                    st.session_state.ip_info = get_ip_info()
            
            config = {
                "offset_x": offset_x,
                "offset_y": offset_y,
                "sig_width": sig_width,
                "sig_height": sig_height
            }
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            signed_files = {}
            sheets_saved_count = 0
            
            for idx, uploaded_file in enumerate(uploaded_files):
                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                
                file_bytes = uploaded_file.getvalue()
                
                position_info = find_name_position(file_bytes)
                
                result = sign_pdf(file_bytes, sig_path, position_info, config)
                
                if result["success"]:
                    name, ext = os.path.splitext(uploaded_file.name)
                    output_name = f"{name}_signed{ext}"
                    
                    signed_files[output_name] = result["output_bytes"].getvalue()
                    
                    record = {
                        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "input_file": uploaded_file.name,
                        "output_file": output_name,
                        "ip_info": st.session_state.ip_info,
                        "position": result["position"],
                        "detection_method": result["detection"]
                    }
                    if save_record(record):
                        sheets_saved_count += 1
                else:
                    st.error(f"Failed to sign {uploaded_file.name}: {result.get('error', 'Unknown error')}")
            
            st.session_state.signed_files = signed_files
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Signed {len(signed_files)} PDF(s) successfully!")
            if GOOGLE_SHEETS_AVAILABLE and sheets_saved_count > 0:
                st.info(f"💾 {sheets_saved_count} record(s) saved to Google Sheets and local backup")
            else:
                st.info("💾 Records saved to local file")
    
    if st.session_state.signed_files:
        st.subheader("📥 Download Signed PDFs")
        
        cols = st.columns(min(3, len(st.session_state.signed_files)))
        for idx, (filename, filedata) in enumerate(st.session_state.signed_files.items()):
            with cols[idx % len(cols)]:
                st.download_button(
                    label=f"📄 {filename[:20]}...",
                    data=filedata,
                    file_name=filename,
                    mime="application/pdf",
                    key=f"dl_{idx}"
                )
        
        if len(st.session_state.signed_files) > 1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, filedata in st.session_state.signed_files.items():
                    zip_file.writestr(filename, filedata)
            zip_buffer.seek(0)
            
            st.download_button(
                label="📦 Download All as ZIP",
                data=zip_buffer.getvalue(),
                file_name="signed_pdfs.zip",
                mime="application/zip",
                key="dl_zip"
            )

# Records section
st.markdown("---")
st.subheader("📋 Signing Records")

if GOOGLE_SHEETS_AVAILABLE:
    status, _ = get_sheets_status()
    if status == "connected_service_account":
        if st.button("🔄 Refresh from Google Sheets"):
            st.cache_data.clear()
            st.rerun()

records = load_all_records()
st.session_state.sign_records = records

if records:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write(f"Total records: **{len(records)}**")
    with col2:
        if GOOGLE_SHEETS_AVAILABLE:
            status, _ = get_sheets_status()
            if status == "connected_service_account":
                st.write(f"Source: Google Sheets ({DATA_SHEET_NAME})")
            elif status == "connected_public":
                st.write(f"Source: Local file (Public Sheet - read only)")
            else:
                st.write(f"Source: Local file ({DEFAULT_CONFIG['record_file']})")
        else:
            st.write(f"Source: {DEFAULT_CONFIG['record_file']}")
    
    if isinstance(records[0], dict):
        if "Input File" in records[0]:
            st.dataframe(records, use_container_width=True)
        else:
            record_data = []
            for r in records:
                record_data.append({
                    "Time": r.get("timestamp", ""),
                    "Input File": r.get("input_file", "")[:30] + "..." if len(r.get("input_file", "")) > 30 else r.get("input_file", ""),
                    "IP": r.get("ip_info", {}).get("public_ip", ""),
                    "Location": f"{r.get('ip_info', {}).get('city', '')}, {r.get('ip_info', {}).get('country', '')}",
                    "Method": r.get("detection_method", "")
                })
            st.dataframe(record_data, use_container_width=True)
    
    with st.expander("View Raw Records (JSON)"):
        st.code(json.dumps(records, indent=2, ensure_ascii=False), language="json")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download Records (JSON)",
            data=json.dumps(records, indent=2, ensure_ascii=False),
            file_name="sign_records.json",
            mime="application/json"
        )
    with col2:
        st.download_button(
            label="📥 Download Records (TXT)",
            data=json.dumps(records, indent=2, ensure_ascii=False),
            file_name="sign_records.txt",
            mime="text/plain"
        )
else:
    st.info("No signing records yet. Sign some PDFs to see records here.")

st.markdown("---")
st.caption("PDF Batch Signature App - Records saved locally (Google Sheets optional)")
