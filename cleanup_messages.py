#!/usr/bin/env python3
# cleanup_messages.py
# Script to clean and standardize extracted message data

import os
import sys
import csv
import re
import logging
import unicodedata
import uuid
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup_messages.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
INPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\input"
OUTPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\input"
INPUT_FILE = os.path.join(INPUT_DIR, "tia_case_messages.csv")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "tia_case_messages_cleaned.csv")

# Target phone numbers (normalized format)
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

def standardize_timestamp(timestamp_str):
    """
    Convert various timestamp formats to YYYY-MM-DD HH:MM:SS
    """
    if not timestamp_str or timestamp_str.strip() == '':
        return None
    
    # Common timestamp formats in the data
    formats = [
        '%d/%m/%Y %H:%M',      # 13/03/2021 9:19
        '%d/%m/%Y %H:%M:%S',    # 13/03/2021 9:19:00
        '%Y-%m-%d %H:%M:%S',    # 2021-03-13 09:19:00
        '%Y-%m-%d %H:%M',       # 2021-03-13 09:19
        '%m/%d/%Y %H:%M:%S',    # 3/13/2021 9:19:00
        '%m/%d/%Y %H:%M'        # 3/13/2021 9:19
    ]
    
    # Try each format
    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_str.strip(), fmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
    
    # If none of the formats match, log and return original
    logger.warning(f"Could not parse timestamp: {timestamp_str}")
    return timestamp_str

def fix_encoding(text):
    """
    Fix common encoding issues in message text
    """
    if not text or text.strip() == '':
        return text
    
    # Pre-process: Try different normalizations to catch issues
    original_text = text
    
    # First normalize to decomposed form (helps with certain encoding issues)
    text = unicodedata.normalize('NFD', text)
    
    # Then normalize to composed form
    text = unicodedata.normalize('NFC', text)
    
    # Comprehensive list of UTF-8 encoding issues and their replacements
    replacements = {
        # Apostrophes and single quotes
        'â€™': "'",    # Common UTF-8 encoding issue for apostrophe
        'â': "'",      # Partial encoding issue
        'â€™': "'",    # Another variant
        '\u2018': "'", # Left single quote
        '\u2019': "'", # Right single quote
        '`': "'",      # Backtick sometimes used as quote
        
        # Double quotes
        'â€œ': '"',    # Opening double quote
        'â€': '"',     # Closing double quote
        'â€"': '"',    # Another variant
        '\u201C': '"', # Left double quote
        '\u201D': '"', # Right double quote
        
        # Dashes
        'â€"': '-',    # Em dash
        'â€"': '-',    # En dash
        '—': '-',      # Em dash
        '–': '-',      # En dash
        
        # Other special characters
        'â€¦': '...',  # Ellipsis
        '…': '...',    # Ellipsis character
        '\xa0': ' ',   # Non-breaking space
        '\u2028': ' ', # Line separator
        '\u2029': ' ', # Paragraph separator
        
        # Common HTML entities that might appear
        '&apos;': "'",
        '&quot;': '"',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&nbsp;': ' ',
    }
    
    # Fix encoding issues
    fixed_text = text
    
    # First pass: direct replacements
    for bad, good in replacements.items():
        if bad in fixed_text:
            fixed_text = fixed_text.replace(bad, good)
    
    # Second pass: handle multi-byte sequence problems using regular expressions
    # This pattern can catch broken UTF-8 sequences that show as multiple characters
    fixed_text = re.sub(r'â€[™"]', "'", fixed_text)
    fixed_text = re.sub(r'â€œ', '"', fixed_text)
    fixed_text = re.sub(r'â€', '"', fixed_text)
    
    # Normalize unicode characters to canonical form for consistency
    fixed_text = unicodedata.normalize('NFKC', fixed_text)
    
    # Log if changes were made
    if fixed_text != original_text:
        logger.debug(f"Fixed encoding: '{original_text}' -> '{fixed_text}'")
    
    return fixed_text

def standardize_direction(direction):
    """
    Convert various direction values to incoming/outgoing
    """
    if not direction:
        return 'unknown'
    
    direction = direction.lower().strip()
    
    # Map common direction values
    if direction in ('received', 'inbound', 'in', 'incoming'):
        return 'incoming'
    elif direction in ('sent', 'outbound', 'out', 'outgoing'):
        return 'outgoing'
    else:
        logger.warning(f"Unknown direction value: {direction}")
        return 'unknown'

def normalize_phone_number(phone):
    """Normalize phone numbers to standard format."""
    if not phone or phone.strip() == '':
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

def clean_messages():
    """
    Clean and standardize the message data
    """
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        return False
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    try:
        # Read input CSV
        with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
        
        logger.info(f"Read {len(rows)} rows from {INPUT_FILE}")
        
        # Check if required columns exist
        required_columns = ['timestamp', 'from_number', 'message_text', 'direction']
        missing_columns = [col for col in required_columns if col not in headers]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Clean and standardize each row
        cleaned_rows = []
        for i, row in enumerate(rows):
            try:
                # Skip rows with empty message text
                if not row['message_text'] or row['message_text'].strip() == '':
                    logger.debug(f"Skipping row {i+2} due to empty message text")
                    continue
                
                # Clean timestamp
                cleaned_timestamp = standardize_timestamp(row['timestamp'])
                if not cleaned_timestamp:
                    logger.warning(f"Skipping row {i+2} due to invalid timestamp: {row['timestamp']}")
                    continue
                
                # Clean message text
                cleaned_message = fix_encoding(row['message_text'])
                
                # If message still contains encoding issues, try more aggressive cleanup
                if 'â€' in cleaned_message:
                    logger.warning(f"Row {i+2} still has encoding issues after initial cleanup")
                    # Try additional cleanup steps
                    cleaned_message = cleaned_message.encode('ascii', 'ignore').decode('ascii')
                    cleaned_message = re.sub(r'[^\x00-\x7F]+', '', cleaned_message)  # Remove non-ASCII
                
                # Standardize direction
                cleaned_direction = standardize_direction(row['direction'])
                
                # Normalize phone numbers
                cleaned_from = normalize_phone_number(row['from_number'])
                cleaned_to = normalize_phone_number(row.get('to_number', '')) if 'to_number' in row else None
                
                # Skip if neither from nor to is in our target list
                if cleaned_from not in TARGET_NUMBERS and cleaned_to not in TARGET_NUMBERS:
                    logger.debug(f"Skipping row {i+2} as numbers {cleaned_from}/{cleaned_to} not in target list")
                    continue
                
                # Generate a unique message ID
                message_id = str(uuid.uuid4())
                
                # Create cleaned row
                cleaned_row = {
                    'message_id': message_id,
                    'timestamp': cleaned_timestamp,
                    'from_number': cleaned_from,
                    'to_number': cleaned_to if cleaned_to else '',
                    'direction': cleaned_direction,
                    'message_text': cleaned_message,
                    'message_type': row.get('message_type', 'SMS')
                }
                
                cleaned_rows.append(cleaned_row)
                
            except Exception as e:
                logger.error(f"Error processing row {i+2}: {e}")
                logger.debug(f"Problematic row: {row}")
        
        logger.info(f"Cleaned {len(cleaned_rows)} rows")
        
        # Sort by timestamp
        try:
            sorted_rows = sorted(cleaned_rows, key=lambda x: x['timestamp'])
            logger.info("Successfully sorted rows by timestamp")
        except Exception as e:
            logger.warning(f"Error sorting by timestamp: {e}")
            sorted_rows = cleaned_rows
        
        # Write output CSV
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['message_id', 'timestamp', 'from_number', 'to_number', 'direction', 'message_text', 'message_type']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sorted_rows)
        
        logger.info(f"Successfully wrote {len(sorted_rows)} rows to {OUTPUT_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return False

def main():
    """Main function to run the script."""
    logger.info("Starting message cleanup")
    
    # Print script information
    print("Message Cleanup Tool")
    print("===================")
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print("Starting cleanup...")
    
    # Run cleanup
    success = clean_messages()
    
    if success:
        logger.info("Message cleanup completed successfully")
        print("\nCleanup completed successfully!")
    else:
        logger.error("Message cleanup failed")
        print("\nCleanup failed. Check log file for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

