#!/usr/bin/env python3
# extract_messages.py
# Script to extract and filter iPhone messages from backup files

import os
import sys
import csv
import re
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_messages.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
BACKUP_DIR = r"C:\Users\admin\Documents\iPhoneBackupExtracts"
OUTPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\input"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "tia_case_messages.csv")

# Target phone numbers to filter (already normalized)
TARGET_NUMBERS = [
    "+61427444440",  # from +61 427 444 440
    "TLSPayphone",   # special case
    "+61488180171",  # from +61 488 180 171
    "+61404720244",  # from +61 404 720 244
    "+61439447043",  # from +61 439 447 043
    "+61436595509",  # from +61 436 595 509
    "+61432654627",  # from +61 432 654 627
    "+61437816851",  # from +61 437 816 851
]

# Files to check
MESSAGE_FILES = [
    os.path.join(BACKUP_DIR, "messages_by_contact.csv"),
    os.path.join(BACKUP_DIR, "sms_export.csv"),
    os.path.join(BACKUP_DIR, "both_numbers_messages.csv"),
]

def normalize_phone_number(phone):
    """Normalize phone numbers to standard format."""
    if phone is None:
        return None
    
    # Handle special case
    if "TLSPayphone" in phone:
        return "TLSPayphone"
    
    # Remove all non-numeric characters except the + prefix
    digits_only = re.sub(r'[^\d+]', '', phone)
    
    # Handle Australian numbers
    if digits_only.startswith('+61'):
        return digits_only
    elif digits_only.startswith('61'):
        return f"+{digits_only}"
    elif digits_only.startswith('0'):
        # Convert Australian local format to international
        return f"+61{digits_only[1:]}"
    else:
        # Return as is if not matching known patterns
        return digits_only

def detect_csv_format(file_path):
    """Detect the format of the CSV file by examining headers."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Read first line to get headers
            dialect = csv.Sniffer().sniff(f.readline())
            f.seek(0)
            reader = csv.reader(f, dialect)
            headers = next(reader, None)
            
            if not headers:
                logger.error(f"No headers found in {file_path}")
                return None
            
            logger.info(f"Found headers in {file_path}: {headers}")
            return {
                'path': file_path,
                'headers': headers,
                'dialect': dialect
            }
    except Exception as e:
        logger.error(f"Error detecting CSV format in {file_path}: {e}")
        return None

def map_headers(headers):
    """Map different header formats to our standardized format."""
    # Common header mappings
    header_map = {
        # Timestamp fields
        'timestamp': ['timestamp', 'date', 'time', 'datetime'],
        
        # From number fields
        'from_number': ['from_number', 'from', 'sender', 'source', 'phone_number'],
        
        # To number fields
        'to_number': ['to_number', 'to', 'recipient', 'destination'],
        
        # Direction fields
        'direction': ['direction', 'type', 'message_direction'],
        
        # Message text fields
        'message_text': ['message_text', 'text', 'body', 'content', 'message'],
        
        # Message type fields
        'message_type': ['message_type', 'type', 'service']
    }
    
    # Create a mapping from the file's headers to our standardized headers
    mapping = {}
    for our_header, possible_headers in header_map.items():
        for header in headers:
            if header.lower() in [h.lower() for h in possible_headers]:
                mapping[our_header] = header
                break
    
    # Log the mapping
    logger.info(f"Header mapping: {mapping}")
    return mapping

def is_target_number(number):
    """Check if a number is in our target list."""
    normalized = normalize_phone_number(number)
    return normalized in TARGET_NUMBERS

def extract_messages():
    """Extract messages from backup files."""
    all_messages = []
    total_found = 0
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for file_path in MESSAGE_FILES:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            continue
        
        logger.info(f"Processing file: {file_path}")
        
        # Detect format
        format_info = detect_csv_format(file_path)
        if not format_info:
            continue
        
        # Map headers
        header_mapping = map_headers(format_info['headers'])
        
        # Check if we have the minimum required headers
        required_headers = ['timestamp', 'from_number', 'message_text']
        missing_headers = [h for h in required_headers if h not in header_mapping]
        
        if missing_headers:
            logger.warning(f"Missing required headers in {file_path}: {missing_headers}")
            continue
        
        # Read messages
        messages_from_file = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f, format_info['dialect'])
                next(reader)  # Skip header
                
                for i, row in enumerate(reader, 1):
                    try:
                        if i % 10000 == 0:
                            logger.info(f"Processed {i} rows from {file_path}")
                        
                        # Create a dictionary from the row
                        row_dict = {header: row[i] for i, header in enumerate(format_info['headers']) if i < len(row)}
                        
                        # Get values using our mapping
                        from_number = row_dict.get(header_mapping.get('from_number', ''), '')
                        
                        # Check to_number if from_number is not in target list
                        to_number = None
                        if 'to_number' in header_mapping:
                            to_number = row_dict.get(header_mapping['to_number'], '')
                        
                        # Check if either from_number or to_number is in our target list
                        if is_target_number(from_number) or is_target_number(to_number):
                            timestamp = row_dict.get(header_mapping['timestamp'], '')
                            message_text = row_dict.get(header_mapping['message_text'], '')
                            
                            # Get direction or infer it
                            direction = None
                            if 'direction' in header_mapping:
                                direction = row_dict.get(header_mapping['direction'], '')
                            else:
                                # Infer direction based on from_number
                                direction = 'incoming' if is_target_number(from_number) else 'outgoing'
                            
                            # Get message_type or use default
                            message_type = None
                            if 'message_type' in header_mapping:
                                message_type = row_dict.get(header_mapping['message_type'], 'SMS')
                            else:
                                message_type = 'SMS'  # Default
                            
                            # Normalize phone numbers
                            normalized_from = normalize_phone_number(from_number)
                            normalized_to = normalize_phone_number(to_number) if to_number else None
                            
                            message = {
                                'timestamp': timestamp,
                                'from_number': normalized_from,
                                'to_number': normalized_to,
                                'direction': direction,
                                'message_text': message_text,
                                'message_type': message_type,
                                'source_file': os.path.basename(file_path)
                            }
                            
                            messages_from_file.append(message)
                    except Exception as e:
                        logger.error(f"Error processing row {i} in {file_path}: {e}")
            
            logger.info(f"Found {len(messages_from_file)} matching messages in {file_path}")
            all_messages.extend(messages_from_file)
            total_found += len(messages_from_file)
            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
    
    # Remove duplicates based on timestamp and message_text
    unique_messages = {}
    for msg in all_messages:
        key = (msg['timestamp'], msg['from_number'], msg['message_text'])
        unique_messages[key] = msg
    
    deduplicated_messages = list(unique_messages.values())
    logger.info(f"After deduplication: {len(deduplicated_messages)} messages")
    
    # Sort by timestamp
    try:
        sorted_messages = sorted(deduplicated_messages, key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'))
    except ValueError:
        logger.warning("Could not sort by timestamp due to format variations. Using original order.")
        sorted_messages = deduplicated_messages
    
    # Write to output file
    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['timestamp', 'from_number', 'to_number', 'direction', 'message_text', 'message_type']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for message in sorted_messages:
                # Only write our standard fields
                filtered_message = {field: message.get(field, '') for field in fieldnames}
                writer.writerow(filtered_message)
        
        logger.info(f"Successfully wrote {len(sorted_messages)} messages to {OUTPUT_FILE}")
        print(f"Extracted {len(sorted_messages)} messages from {total_found} matching messages.")
        print(f"Output saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"Error writing to output file: {e}")
        print(f"Error: {e}")
        return False
    
    return True

def main():
    """Main function to run the script."""
    logger.info("Starting message extraction")
    
    # Print script information
    print("iPhone Message Extraction Tool")
    print("==============================")
    print(f"Target numbers: {', '.join(TARGET_NUMBERS)}")
    print(f"Backup directory: {BACKUP_DIR}")
    print(f"Output file: {OUTPUT_FILE}")
    print("Starting extraction...")
    
    # Run extraction
    success = extract_messages()
    
    if success:
        logger.info("Message extraction completed successfully")
        print("\nExtraction completed successfully!")
    else:
        logger.error("Message extraction failed")
        print("\nExtraction failed. Check log file for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

