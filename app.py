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

st.set_page_config(page_title="PDF Batch Signature App", layout="wide")

# Default configuration
DEFAULT_CONFIG = {
    "offset_x": -90,
    "offset_y": -80,
    "sig_width": 70,
    "sig_height": 70,
    "signature_path": "signature.png",
    "record_file": "sign_records.txt"  # Save as .txt file
}

st.title("📄 PDF Batch Signature App")
st.markdown("Upload multiple PDF files to sign them automatically")


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
        # Calculate signature position
        if position_info["found"]:
            sig_x = position_info["khoa_x"] + config["offset_x"]
            sig_y = position_info["khoa_y"] + config["offset_y"]
            detection_status = "auto"
        else:
            # Default fallback position
            sig_x = 340
            sig_y = 440
            detection_status = "manual_fallback"
        
        # Open PDF and add signature
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


def load_records_from_file():
    """Load existing records from local file."""
    record_file = DEFAULT_CONFIG["record_file"]
    if os.path.exists(record_file):
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Could not load records file: {e}")
            return []
    return []


def save_record_to_file(record):
    """Save a record to local file."""
    records = load_records_from_file()
    records.append(record)
    
    record_file = DEFAULT_CONFIG["record_file"]
    try:
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Failed to save record: {e}")
        return False


def load_records():
    """Load records from session state or file."""
    if "sign_records" not in st.session_state:
        st.session_state.sign_records = load_records_from_file()
    return st.session_state.sign_records


def save_record(record):
    """Save a record to both session state and file."""
    # Add to session state
    records = load_records()
    records.append(record)
    st.session_state.sign_records = records
    
    # Save to file
    return save_record_to_file(record)


def clear_all_records():
    """Clear records from both session state and file."""
    st.session_state.sign_records = []
    record_file = DEFAULT_CONFIG["record_file"]
    if os.path.exists(record_file):
        try:
            os.remove(record_file)
            return True
        except Exception as e:
            st.error(f"Failed to delete records file: {e}")
            return False
    return True


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

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Signature Position")
    offset_x = st.number_input("Offset X", value=DEFAULT_CONFIG["offset_x"], step=5)
    offset_y = st.number_input("Offset Y", value=DEFAULT_CONFIG["offset_y"], step=5)
    sig_width = st.number_input("Width", value=DEFAULT_CONFIG["sig_width"], step=5)
    sig_height = st.number_input("Height", value=DEFAULT_CONFIG["sig_height"], step=5)
    
    st.subheader("Signature Preview")
    if os.path.exists(DEFAULT_CONFIG["signature_path"]):
        st.image(DEFAULT_CONFIG["signature_path"], width=150)
    else:
        st.error("Signature file not found!")
    
    # IP Info Display
    if st.button("🌐 Get IP Info"):
        with st.spinner("Getting IP info..."):
            st.session_state.ip_info = get_ip_info()
    
    if st.session_state.ip_info:
        st.subheader("🌐 IP Information")
        st.write(f"Public IP: {st.session_state.ip_info['public_ip']}")
        st.write(f"Local IP: {st.session_state.ip_info['local_ip']}")
        st.write(f"Location: {st.session_state.ip_info['city']}, {st.session_state.ip_info['region']}")
        st.write(f"Country: {st.session_state.ip_info['country']}")

# Main content
st.subheader("📤 Upload PDF Files")
uploaded_files = st.file_uploader(
    "Choose PDF files", 
    type="pdf", 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📎 {len(uploaded_files)} file(s) selected")
    
    # Show file list
    with st.expander("View selected files"):
        for file in uploaded_files:
            st.write(f"- {file.name} ({len(file.getvalue())//1024} KB)")
    
    # Process buttons
    col1, col2 = st.columns(2)
    
    with col1:
        preview_file = st.selectbox(
            "Select file to preview",
            [f.name for f in uploaded_files],
            key="preview_select"
        )
        
        if st.button("👁️ Preview Position", use_container_width=True):
            # Get the selected file
            selected_file = next(f for f in uploaded_files if f.name == preview_file)
            file_bytes = selected_file.getvalue()
            
            # Find position
            position_info = find_name_position(file_bytes)
            
            # Create preview
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            page = pdf_document[0]
            
            if position_info["found"]:
                sig_x = position_info["khoa_x"] + offset_x
                sig_y = position_info["khoa_y"] + offset_y
                khoa_x, khoa_y = position_info["khoa_x"], position_info["khoa_y"]
                
                # Draw red rectangle for signature
                rect = fitz.Rect(sig_x, sig_y, sig_x + sig_width, sig_y + sig_height)
                page.draw_rect(rect, color=(1, 0, 0), width=2)
                page.insert_text((sig_x, sig_y - 5), "SIGNATURE", fontsize=8, color=(1, 0, 0))
                
                # Draw crosshair at Khoa
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
            
            for idx, uploaded_file in enumerate(uploaded_files):
                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                
                file_bytes = uploaded_file.getvalue()
                
                # Find position
                position_info = find_name_position(file_bytes)
                
                # Sign PDF
                result = sign_pdf(file_bytes, DEFAULT_CONFIG["signature_path"], position_info, config)
                
                if result["success"]:
                    # Generate output filename
                    name, ext = os.path.splitext(uploaded_file.name)
                    output_name = f"{name}_signed{ext}"
                    
                    signed_files[output_name] = result["output_bytes"].getvalue()
                    
                    # Save record to file
                    record = {
                        "timestamp": datetime.now().isoformat(),
                        "input_file": uploaded_file.name,
                        "output_file": output_name,
                        "ip_info": st.session_state.ip_info,
                        "position": result["position"],
                        "detection_method": result["detection"]
                    }
                    save_record(record)
                else:
                    st.error(f"Failed to sign {uploaded_file.name}: {result.get('error', 'Unknown error')}")
            
            st.session_state.signed_files = signed_files
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Signed {len(signed_files)} PDF(s) successfully!")
            st.info(f"💾 Records saved to: {DEFAULT_CONFIG['record_file']}")
    
    # Show signed files for download
    if st.session_state.signed_files:
        st.subheader("📥 Download Signed PDFs")
        
        # Individual downloads
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
        
        # Download all as ZIP
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

# Load records from file (sync on each render)
records = load_records_from_file()
st.session_state.sign_records = records

if records:
    # Show record count and file info
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write(f"Total records: **{len(records)}**")
    with col2:
        record_file = DEFAULT_CONFIG["record_file"]
        if os.path.exists(record_file):
            file_size = os.path.getsize(record_file)
            st.write(f"File: `{record_file}` ({file_size} bytes)")
        else:
            st.write(f"File: `{record_file}` (not saved yet)")
    with col3:
        if st.button("🗑️ Clear All Records"):
            if clear_all_records():
                st.success("Records cleared!")
                st.rerun()
    
    # Display records table
    record_data = []
    for r in records:
        record_data.append({
            "Time": r["timestamp"][:19] if len(r["timestamp"]) > 19 else r["timestamp"],
            "Input File": r["input_file"][:30] + "..." if len(r["input_file"]) > 30 else r["input_file"],
            "IP": r["ip_info"]["public_ip"],
            "Location": f"{r['ip_info']['city']}, {r['ip_info']['country']}",
            "Method": r["detection_method"]
        })
    
    st.dataframe(record_data, use_container_width=True)
    
    # View raw JSON
    with st.expander("View Raw Records (JSON)"):
        st.code(json.dumps(records, indent=2), language="json")
    
    # Export records
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
    # Show file path even if empty
    st.caption(f"Records will be saved to: `{DEFAULT_CONFIG['record_file']}`")

st.markdown("---")
st.caption("PDF Batch Signature App - Records auto-saved to sign_records.txt")
