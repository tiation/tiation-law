#!/usr/bin/env python3
# organize_evidence.py
# Script to organize sentiment analysis results into evidence categories

import os
import sys
import csv
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('organize_evidence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
INPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\output"
OUTPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\Legal_Evidence"
INPUT_FILE = os.path.join(INPUT_DIR, "local_sentiment_results.csv")

# Evidence category directories
CATEGORIES = {
    "Positive_Relationships": os.path.join(OUTPUT_DIR, "Positive_Relationships"),
    "Parental_Care": os.path.join(OUTPUT_DIR, "Parental_Care"),
    "Child_Welfare": os.path.join(OUTPUT_DIR, "Child_Welfare")
}

# File names for each category
OUTPUT_FILES = {
    "Positive_Relationships": {
        "all": "all_positive_relationship_messages.md",
        "top": "top_positive_relationship_messages.md",
        "timeline": "positive_relationship_timeline.md"
    },
    "Parental_Care": {
        "all": "all_parental_care_messages.md",
        "top": "top_parental_care_messages.md",
        "timeline": "parental_care_timeline.md"
    },
    "Child_Welfare": {
        "all": "all_child_welfare_messages.md",
        "top": "top_child_welfare_messages.md",
        "timeline": "child_welfare_timeline.md"
    }
}

# Create directories if they don't exist
for directory in CATEGORIES.values():
    os.makedirs(directory, exist_ok=True)

def is_true_value(value):
    """Check if a value is considered true, handling both boolean and string types"""
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in ('true', 'yes', 't', 'y', '1')
    elif pd.isna(value):  # Handle NaN values
        return False
    else:
        return bool(value)

def safe_str(value):
    """Safely convert value to string, handling None and NaN values"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)

def safe_split(value, delimiter=','):
    """Safely split a string, handling various data types and empty values"""
    if value is None or pd.isna(value):
        return []
    
    if not isinstance(value, str):
        value = safe_str(value)
        
    if not value or value.strip() == '':
        return []
        
    return value.split(delimiter)

def format_message_for_markdown(message, index=None, include_keywords=True, include_cross_references=True):
    """Format a message as markdown with metadata"""
    result = []
    
    # Add message number if provided
    if index is not None:
        result.append(f"## Message {index}\n")
    
    # Add basic information
    result.append(f"**Date:** {message['timestamp']}")
    result.append(f"**From:** {message['from_number']}")
    result.append(f"**Direction:** {message['direction']}")
    result.append(f"**Sentiment:** {message['sentiment_category']} (score: {float(message['sentiment_compound']):.2f})")
    
    # Add keywords if requested
    if include_keywords:
        keywords = []
        if 'positive_relationship_keywords' in message and not pd.isna(message['positive_relationship_keywords']):
            positive_keywords = safe_split(message['positive_relationship_keywords'])
            if positive_keywords:
                keywords.extend([k for k in positive_keywords if k.strip()])
        
        if 'parental_care_keywords' in message and not pd.isna(message['parental_care_keywords']):
            parental_keywords = safe_split(message['parental_care_keywords'])
            if parental_keywords:
                keywords.extend([k for k in parental_keywords if k.strip()])
                
        if 'child_welfare_keywords' in message and not pd.isna(message['child_welfare_keywords']):
            welfare_keywords = safe_split(message['child_welfare_keywords'])
            if welfare_keywords:
                keywords.extend([k for k in welfare_keywords if k.strip()])
                
        if keywords:
            result.append(f"**Keywords:** {', '.join(keywords)}")
    
    # Add cross-references if requested
    if include_cross_references:
        categories = []
        if message.get('positive_relationship') and is_true_value(message['positive_relationship']):
            categories.append("Positive Relationships")
        if message.get('parental_care') and is_true_value(message['parental_care']):
            categories.append("Parental Care")
        if message.get('child_welfare') and is_true_value(message['child_welfare']):
            categories.append("Child Welfare")
            
        if len(categories) > 1:
            result.append(f"**Also found in:** {', '.join([c for c in categories if c != 'current_category'])}")
    
    # Add message content
    result.append("\n**Message Text:**")
    result.append(f"```\n{message['message_text']}\n```\n")
    
    # Add insights if available
    if message.get('insights') and message['insights']:
        result.append(f"**Analysis Insights:** {message['insights']}\n")
    
    # Add separator
    result.append("---\n")
    
    return "\n".join(result)

def create_category_files(messages, category, message_id_map):
    """Create markdown files for a specific evidence category"""
    category_dir = CATEGORIES[category]
    
    # Determine which messages belong to this category
    if category == "Positive_Relationships":
        category_messages = [m for m in messages if is_true_value(m.get('positive_relationship', False))]
        category_key = 'positive_relationship'
    elif category == "Parental_Care":
        category_messages = [m for m in messages if is_true_value(m.get('parental_care', False))]
        category_key = 'parental_care'
    elif category == "Child_Welfare":
        category_messages = [m for m in messages if is_true_value(m.get('child_welfare', False))]
        category_key = 'child_welfare'
    
    # Sort by sentiment strength (descending)
    sorted_messages = sorted(category_messages, key=lambda x: float(x.get('sentiment_compound', 0)), reverse=True)
    
    # Create "top messages" file (top 20)
    top_messages = sorted_messages[:20]
    top_file_path = os.path.join(category_dir, OUTPUT_FILES[category]["top"])
    
    with open(top_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# Top {category.replace('_', ' ')} Messages\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(f"This file contains the top 20 messages showing {category.replace('_', ' ').lower()}, sorted by sentiment strength.\n\n")
        
        for i, message in enumerate(top_messages, 1):
            # Store message ID for cross-referencing
            message_id = message.get('message_id', f"msg_{i}")
            message_id_map[message_id] = {
                'category': category,
                'rank': i,
                'sentiment': float(message.get('sentiment_compound', 0)),
                'timestamp': message.get('timestamp', ''),
                'snippet': message.get('message_text', '')[:50] + '...' if len(message.get('message_text', '')) > 50 else message.get('message_text', '')
            }
            
            f.write(format_message_for_markdown(message, i))
    
    # Create "all messages" file
    all_file_path = os.path.join(category_dir, OUTPUT_FILES[category]["all"])
    
    with open(all_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# All {category.replace('_', ' ')} Messages\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(f"This file contains all {len(category_messages)} messages showing {category.replace('_', ' ').lower()}, sorted by sentiment strength.\n\n")
        
        for i, message in enumerate(sorted_messages, 1):
            # Store message ID for cross-referencing
            message_id = message.get('message_id', f"msg_{i}")
            if message_id not in message_id_map:
                message_id_map[message_id] = {
                    'category': category,
                    'rank': i,
                    'sentiment': float(message.get('sentiment_compound', 0)),
                    'timestamp': message.get('timestamp', ''),
                    'snippet': message.get('message_text', '')[:50] + '...' if len(message.get('message_text', '')) > 50 else message.get('message_text', '')
                }
            
            f.write(format_message_for_markdown(message, i))
    
    # Create timeline file
    timeline_messages = sorted(category_messages, key=lambda x: x.get('timestamp', ''))
    timeline_file_path = os.path.join(category_dir, OUTPUT_FILES[category]["timeline"])
    
    with open(timeline_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# {category.replace('_', ' ')} Timeline\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(f"This file contains all {len(category_messages)} messages showing {category.replace('_', ' ').lower()}, sorted chronologically.\n\n")
        
        current_month = None
        for i, message in enumerate(timeline_messages, 1):
            # Add month/year headers for organization
            try:
                timestamp = datetime.strptime(message.get('timestamp', ''), '%Y-%m-%d %H:%M:%S')
                month_year = timestamp.strftime('%B %Y')
                
                if month_year != current_month:
                    f.write(f"## {month_year}\n\n")
                    current_month = month_year
            except:
                pass
            
            f.write(format_message_for_markdown(message, i))
    
    # Create keyword summary file
    keyword_file_path = os.path.join(category_dir, f"{category.lower()}_keywords.md")
    
    with open(keyword_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# {category.replace('_', ' ')} Keywords Analysis\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        # Count keyword frequencies
        keyword_counts = defaultdict(int)
        keyword_field = f"{category_key}_keywords"
        
        for message in category_messages:
            if keyword_field in message and not pd.isna(message[keyword_field]):
                keywords = safe_split(message[keyword_field])
                for keyword in keywords:
                    if keyword.strip():
                        keyword_counts[keyword.strip()] += 1
        
        # Sort keywords by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        
        f.write("## Keyword Frequency\n\n")
        f.write("| Keyword | Frequency | Percentage |\n")
        f.write("|---------|-----------|------------|\n")
        
        for keyword, count in sorted_keywords:
            percentage = (count / len(category_messages)) * 100
            f.write(f"| {keyword} | {count} | {percentage:.1f}% |\n")

def create_cross_reference_file(message_id_map):
    """Create a cross-reference file for messages appearing in multiple categories"""
    # Find messages that appear in multiple categories
    messages_by_id = defaultdict(list)
    
    for message_id, info in message_id_map.items():
        messages_by_id[message_id].append(info)
    
    # Filter for messages in multiple categories
    multi_category_messages = {msg_id: infos for msg_id, infos in messages_by_id.items() if len(infos) > 1}
    
    if not multi_category_messages:
        return
    
    # Create cross-reference file
    cross_ref_path = os.path.join(OUTPUT_DIR, "cross_category_messages.md")
    
    with open(cross_ref_path, 'w', encoding='utf-8') as f:
        f.write("# Messages Appearing in Multiple Evidence Categories\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(f"This file contains {len(multi_category_messages)} messages that appear in multiple evidence categories, providing stronger overall evidence.\n\n")
        
        for msg_id, infos in multi_category_messages.items():
            categories = [info['category'].replace('_', ' ') for info in infos]
            f.write(f"## Message ID: {msg_id}\n\n")
            f.write(f"**Categories:** {', '.join(categories)}\n")
            
            # Use the first info item for shared details
            primary_info = infos[0]
            f.write(f"**Date:** {primary_info['timestamp']}\n")
            f.write(f"**Sentiment Score:** {primary_info['sentiment']:.2f}\n")
            f.write(f"**Snippet:** {primary_info['snippet']}\n\n")
            
            # Add links to each category's files
            f.write("**View in category files:**\n")
            for info in infos:
                category = info['category']
                rank = info['rank']
                f.write(f"- [{category.replace('_', ' ')}]({category}/all_{category.lower()}_messages.md) (#{rank})\n")
            
            f.write("\n---\n\n")

def create_evidence_index():
    """Create an index file for all evidence files"""
    index_path = os.path.join(OUTPUT_DIR, "EVIDENCE_INDEX.md")
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("# Evidence Index\n\n")
        f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("This file provides a comprehensive index of all evidence files organized by category.\n\n")
        
        # Add summary reports
        f.write("## Summary Reports\n\n")
        f.write("- [Executive Summary](Summary_Reports/summary_key_findings.md) - Key findings for legal team\n")
        f.write("- [Detailed Analysis Report](Summary_Reports/local_sentiment_summary.md) - Comprehensive technical analysis\n")
        f.write("- [Cross-Category Messages](cross_category_messages.md) - Messages appearing in multiple evidence categories\n\n")
        
        # Add category files
        for category, files in OUTPUT_FILES.items():
            f.write(f"## {category.replace('_', ' ')}\n\n")
            f.write(f"- [Top Messages]({category}/{files['top']}) - Top 20 messages ranked by sentiment strength\n")
            f.write(f"- [Timeline]({category}/{files['timeline']}) - Chronological view of all messages\n")
            f.write(f"- [All Messages]({category}/{files['all']}) - Complete collection of messages\n")
            f.write(f"- [Keyword Analysis]({category}/{category.lower()}_keywords.md) - Analysis of frequently occurring keywords\n\n")

def main():
    """Main function to organize evidence"""
    logger.info("Starting evidence organization")
    
    # Print script information
    print("Evidence Organization Tool")
    print("=========================")
    print(f"Input file: {INPUT_FILE}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Starting organization...")
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        print(f"Error: Input file not found: {INPUT_FILE}")
        return 1
    
    try:
        # Load input data with appropriate type conversions
        df = pd.read_csv(INPUT_FILE)
        
        # Convert boolean columns
        boolean_columns = ['positive_relationship', 'parental_care', 'child_welfare']
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        # Handle NaN values in keyword columns
        keyword_columns = [
            'positive_relationship_keywords', 
            'parental_care_keywords', 
            'child_welfare_keywords'
        ]
        for col in keyword_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
        
        messages = df.to_dict('records')
        logger.info(f"Loaded {len(messages)} messages from {INPUT_FILE}")
        
        # Create message ID map for cross-referencing
        message_id_map = {}
        
        # Create files for each category
        for category in CATEGORIES:
            print(f"Processing {category} messages...")
            create_category_files(messages, category, message_id_map)
            logger.info(f"Created files for {category}")
        
        # Create cross-reference file
        print("Creating cross-reference file...")
        create_cross_reference_file(message_id_map)
        logger.info("Created cross-reference file")
        
        # Create evidence index
        print("Creating evidence index...")
        create_evidence_index()
        logger.info("Created evidence index")
        
        logger.info("Evidence organization completed")
        print("\nEvidence organization completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Error in evidence organization: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

