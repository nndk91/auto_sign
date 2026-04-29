#!/usr/bin/env python3
"""
Auto Sign PDF Batch Processor
Signs multiple PDFs automatically and tracks records with IP location.
"""

import pdfplumber
import fitz  # PyMuPDF
import os
import glob
import json
import socket
import requests
from datetime import datetime
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "offset_x": -90,
    "offset_y": -80,
    "sig_width": 70,
    "sig_height": 70,
    "signature_path": "signature.png",
    "output_suffix": "_signed",
    "record_file": "sign_records.json"
}


def get_ip_info():
    """Get IP address and location information."""
    try:
        # Get public IP
        ip_response = requests.get("https://api.ipify.org?format=json", timeout=5)
        public_ip = ip_response.json().get("ip", "unknown")
        
        # Get location info
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


def find_name_position(pdf_path):
    """Find the position of 'Nguyen Ngoc Dang Khoa' in the PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
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
        print(f"Error reading {pdf_path}: {e}")
    
    return {"found": False}


def sign_pdf(input_path, output_path, signature_path, position_info, config):
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
        pdf_document = fitz.open(input_path)
        page = pdf_document[0]
        
        rect = fitz.Rect(
            sig_x, 
            sig_y, 
            sig_x + config["sig_width"], 
            sig_y + config["sig_height"]
        )
        
        page.insert_image(rect, filename=signature_path)
        pdf_document.save(output_path)
        pdf_document.close()
        
        return {
            "success": True,
            "detection": detection_status,
            "position": {"x": sig_x, "y": sig_y},
            "input_file": os.path.basename(input_path),
            "output_file": os.path.basename(output_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "input_file": os.path.basename(input_path)
        }


def load_records(record_file):
    """Load existing records."""
    if os.path.exists(record_file):
        try:
            with open(record_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_records(records, record_file):
    """Save records to file."""
    with open(record_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def main():
    """Main batch processing function."""
    print("=" * 60)
    print("PDF AUTO SIGN BATCH PROCESSOR")
    print("=" * 60)
    print()
    
    config = DEFAULT_CONFIG
    
    # Check if signature file exists
    if not os.path.exists(config["signature_path"]):
        print(f"❌ Error: Signature file '{config['signature_path']}' not found!")
        return
    
    # Get IP info
    print("[INFO] Getting IP location information...")
    ip_info = get_ip_info()
    print(f"   Public IP: {ip_info['public_ip']}")
    print(f"   Location: {ip_info['city']}, {ip_info['region']}, {ip_info['country']}")
    print()
    
    # Find all PDF files (excluding already signed ones)
    pdf_files = sorted([f for f in glob.glob("PO *.pdf") if "_signed" not in f and "_test" not in f])
    
    if not pdf_files:
        print("[ERROR] No PDF files found to process!")
        return
    
    print(f"[FILES] Found {len(pdf_files)} PDF file(s) to process:")
    for pdf in pdf_files:
        print(f"   - {pdf}")
    print()
    
    # Display configuration
    print("[CONFIG] Settings:")
    print(f"   Offset X: {config['offset_x']}")
    print(f"   Offset Y: {config['offset_y']}")
    print(f"   Width: {config['sig_width']}")
    print(f"   Height: {config['sig_height']}")
    print()
    
    # Load existing records
    records = load_records(config["record_file"])
    
    # Process each PDF
    success_count = 0
    failed_count = 0
    
    print("[PROCESS] Signing files...")
    print("-" * 60)
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"  {filename}...", end=" ")
        
        # Find name position
        position_info = find_name_position(pdf_path)
        
        # Generate output filename
        name, ext = os.path.splitext(filename)
        output_path = f"{name}{config['output_suffix']}{ext}"
        
        # Sign the PDF
        result = sign_pdf(pdf_path, output_path, config["signature_path"], position_info, config)
        
        if result["success"]:
            print(f"OK [{result['detection']}]")
            success_count += 1
            
            # Create record
            record = {
                "timestamp": datetime.now().isoformat(),
                "input_file": result["input_file"],
                "output_file": result["output_file"],
                "ip_info": ip_info,
                "position": result["position"],
                "detection_method": result["detection"]
            }
            records.append(record)
        else:
            print(f"FAILED - {result.get('error', 'Unknown error')}")
            failed_count += 1
    
    print("-" * 60)
    
    # Save records
    save_records(records, config["record_file"])
    
    # Summary
    print()
    print("[SUMMARY]")
    print(f"   Signed: {success_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Total records: {len(records)}")
    print(f"   Records file: {config['record_file']}")
    print()
    print("=" * 60)
    print("Batch processing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
