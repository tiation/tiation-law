#!/usr/bin/env python3
# run_sentiment_analysis.py
# Script to analyze cleaned messages for legal evidence

import os
import sys
import csv
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import pandas as pd
import openai
from dotenv import load_dotenv

# Import configuration
sys.path.append(os.path.join(os.path.dirname(__file__), 'sentiment_analysis'))
try:
    from sentiment_analysis.config import (
        API_CONFIG, 
        BATCH_CONFIG, 
        ANALYSIS_CONFIG, 
        CSV_CONFIG
    )
except ImportError:
    from config import API_CONFIG, BATCH_CONFIG, ANALYSIS_CONFIG, CSV_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sentiment_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
INPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\input"
OUTPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\output"
INPUT_FILE = os.path.join(INPUT_DIR, "tia_case_messages_cleaned.csv")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "sentiment_analysis_results.csv")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "legal_evidence_summary.md")

# Target phone numbers for analysis (using more descriptive names)
PHONE_NUMBERS = {
    "TIA": "+61427444440",  # Primary subject of defense
    "PAYPHONE": "TLSPayphone",  # Payphone communications
    "CONTACT_1": "+61488180171",
    "CONTACT_2": "+61404720244",
    "CONTACT_3": "+61439447043",
    "CONTACT_4": "+61436595509",
    "CONTACT_5": "+61432654627",
    "CONTACT_6": "+61437816851"
}

# Initialize OpenAI API
def init_openai():
    """Initialize OpenAI API with configuration"""
    # Load .env file explicitly from the current directory
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    
    # Try to get API key from different sources
    openai.api_key = os.getenv("OPENAI_API_KEY") or API_CONFIG.get("api_key")
    
    if not openai.api_key:
        logger.error("OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
        sys.exit(1)
        
    logger.info("OpenAI API initialized")

# Rate limiting helper
class RateLimiter:
    """Helper class to handle API rate limiting"""
    def __init__(self, requests_per_minute):
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self.min_interval = 60.0 / requests_per_minute

    def wait_if_needed(self):
        """Wait if we're exceeding the rate limit"""
        current_time = time.time()
        
        # Remove old requests from the tracking list
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # If we've hit the limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = min(self.request_times)
            time_to_wait = max(0, 60 - (current_time - oldest_request))
            if time_to_wait > 0:
                logger.debug(f"Rate limit reached. Waiting {time_to_wait:.2f} seconds.")
                time.sleep(time_to_wait)
        
        # Add this request to the tracking list
        self.request_times.append(time.time())

# Analyze message sentiment
def analyze_message(message, phone_number, rate_limiter):
    """
    Analyze the sentiment and beliefs in a message
    """
    # Skip empty messages
    if not message or message.strip() == '':
        return None, None
    
    # Wait if needed for rate limiting
    rate_limiter.wait_if_needed()
    
    # Prepare the prompt for sentiment analysis
    sentiment_prompt = ANALYSIS_CONFIG["sentiment_prompt_template"].format(
        message=message,
        target_number=phone_number,
        target_1=PHONE_NUMBERS["TIA"],
        target_2=PHONE_NUMBERS["TIA"]  # Using same target for both prompts in this case
    )
    
    # Call OpenAI API for sentiment analysis
    try:
        sentiment_response = openai.ChatCompletion.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "system", "content": "You are a legal sentiment analyzer focusing on positive evidence."},
                {"role": "user", "content": sentiment_prompt}
            ],
            temperature=API_CONFIG["temperature"],
            max_tokens=API_CONFIG["max_tokens"]
        )
        sentiment_analysis = sentiment_response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in sentiment analysis API call: {e}")
        return None, None
    
    # Wait if needed for rate limiting
    rate_limiter.wait_if_needed()
    
    # Prepare the prompt for beliefs analysis
    beliefs_prompt = ANALYSIS_CONFIG["beliefs_prompt_template"].format(
        message=message,
        target_number=phone_number,
        target_1=PHONE_NUMBERS["TIA"],
        target_2=PHONE_NUMBERS["TIA"]  # Using same target for both prompts in this case
    )
    
    # Call OpenAI API for beliefs analysis
    try:
        beliefs_response = openai.ChatCompletion.create(
            model=API_CONFIG["model"],
            messages=[
                {"role": "system", "content": "You are a legal analyst uncovering positive underlying beliefs."},
                {"role": "user", "content": beliefs_prompt}
            ],
            temperature=API_CONFIG["temperature"],
            max_tokens=API_CONFIG["max_tokens"]
        )
        beliefs_analysis = beliefs_response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in beliefs analysis API call: {e}")
        return sentiment_analysis, None
    
    return sentiment_analysis, beliefs_analysis

# Process messages in batches
def process_messages(messages, batch_size=25, max_retries=3):
    """
    Process messages in batches
    """
    # Create rate limiter
    rate_limiter = RateLimiter(BATCH_CONFIG["rate_limit"]["requests_per_minute"])
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Prepare result dataframe
    results = []
    
    # Process in batches
    total_batches = (len(messages) + batch_size - 1) // batch_size
    logger.info(f"Processing {len(messages)} messages in {total_batches} batches")
    
    # Set up checkpoint file
    checkpoint_file = os.path.join(OUTPUT_DIR, "analysis_checkpoint.json")
    completed_ids = set()
    
    # Load checkpoint if exists
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                completed_ids = set(checkpoint_data.get("completed_ids", []))
                logger.info(f"Loaded checkpoint with {len(completed_ids)} completed messages")
        except Exception as e:
            logger.warning(f"Error loading checkpoint: {e}")
    
    # Track progress
    start_time = time.time()
    processed_count = 0
    success_count = 0
    
    # Process batches with progress bar
    for batch_idx in tqdm(range(0, len(messages), batch_size), desc="Processing batches"):
        batch = messages[batch_idx:batch_idx + batch_size]
        batch_results = []
        
        # Process each message in the batch
        for message in tqdm(batch, desc=f"Batch {batch_idx//batch_size + 1}/{total_batches}", leave=False):
            message_id = message["message_id"]
            
            # Skip if already analyzed
            if message_id in completed_ids:
                logger.debug(f"Skipping already analyzed message: {message_id}")
                continue
            
            # Get message details
            timestamp = message["timestamp"]
            from_number = message["from_number"]
            message_text = message["message_text"]
            direction = message["direction"]
            
            # Skip empty messages
            if not message_text or message_text.strip() == '':
                logger.debug(f"Skipping empty message: {message_id}")
                continue
            
            # Analyze message with retries
            retry_count = 0
            sentiment_analysis = None
            beliefs_analysis = None
            
            while retry_count < max_retries:
                try:
                    sentiment_analysis, beliefs_analysis = analyze_message(
                        message_text, from_number, rate_limiter
                    )
                    if sentiment_analysis or beliefs_analysis:
                        break
                except Exception as e:
                    logger.warning(f"Error analyzing message {message_id} (attempt {retry_count+1}): {e}")
                    retry_count += 1
                    time.sleep(BATCH_CONFIG["retry_delay"])
            
            # Store results
            processed_count += 1
            if sentiment_analysis or beliefs_analysis:
                success_count += 1
                result = {
                    "message_id": message_id,
                    "timestamp": timestamp,
                    "from_number": from_number,
                    "direction": direction,
                    "message_text": message_text,
                    "sentiment": sentiment_analysis or "No sentiment analysis available",
                    "unspoken_positive_beliefs": beliefs_analysis or "No beliefs analysis available"
                }
                batch_results.append(result)
                
                # Add to completed IDs
                completed_ids.add(message_id)
            
            # Save checkpoint at intervals
            if processed_count % ANALYSIS_CONFIG["save_checkpoint_interval"] == 0:
                save_checkpoint(checkpoint_file, completed_ids)
                
                # Also save intermediate results
                all_results = results + batch_results
                save_results_to_csv(all_results)
                logger.info(f"Saved intermediate results: {len(all_results)} entries")
        
        # Add batch results to main results
        results.extend(batch_results)
        
        # Save checkpoint after each batch
        save_checkpoint(checkpoint_file, completed_ids)
    
    # Calculate statistics
    elapsed_time = time.time() - start_time
    logger.info(f"Analysis complete: {success_count}/{processed_count} messages analyzed successfully")
    logger.info(f"Total time: {elapsed_time:.2f} seconds ({elapsed_time/processed_count:.2f} seconds per message)")
    
    return results

# Save checkpoint
def save_checkpoint(checkpoint_file, completed_ids):
    """Save checkpoint of completed message IDs"""
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump({
                "completed_ids": list(completed_ids),
                "timestamp": datetime.now().isoformat()
            }, f)
        logger.debug(f"Saved checkpoint with {len(completed_ids)} completed messages")
    except Exception as e:
        logger.warning(f"Error saving checkpoint: {e}")

# Save results to CSV
def save_results_to_csv(results):
    """Save analysis results to CSV file"""
    if not results:
        logger.warning("No results to save")
        return
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Write to CSV
        df.to_csv(OUTPUT_FILE, index=False, encoding=CSV_CONFIG["encoding"])
        logger.info(f"Saved {len(results)} results to {OUTPUT_FILE}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return False

# Generate summary report
def generate_summary_report(results):
    """Generate summary report highlighting key evidence"""
    if not results:
        logger.warning("No results to summarize")
        return False
    
    try:
        # Count messages by phone number
        number_counts = {}
        for result in results:
            from_number = result["from_number"]
            number_counts[from_number] = number_counts.get(from_number, 0) + 1
        
        # Find key evidence categories
        positive_relationship_evidence = []
        parental_care_evidence = []
        child_welfare_evidence = []
        
        # Simple keyword-based categorization
        relationship_keywords = ["positive", "respect", "care", "goodwill", "peaceful"]
        parental_keywords = ["love", "parent", "child", "care", "nurture"]
        welfare_keywords = ["wellbeing", "welfare", "protect", "safety", "health"]
        
        for result in results:
            sentiment = result.get("sentiment", "").lower()
            beliefs = result.get("unspoken_positive_beliefs", "").lower()
            text = result.get("message_text", "").lower()
            
            # Check for positive relationship evidence
            if any(keyword in sentiment for keyword in relationship_keywords):
                positive_relationship_evidence.append(result)
            
            # Check for parental care evidence
            if any(keyword in sentiment for keyword in parental_keywords):
                parental_care_evidence.append(result)
            
            # Check for child welfare evidence
            if any(keyword in sentiment for keyword in welfare_keywords) or \
               any(keyword in beliefs for keyword in welfare_keywords):
                child_welfare_evidence.append(result)
        
        # Generate report
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            f.write("# Legal Evidence Summary Report\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## Overview\n\n")
            f.write(f"- **Total messages analyzed:** {len(results)}\n")
            f.write(f"- **Messages by phone number:**\n")
            for number, count in number_counts.items():
                # Map to descriptive name if available
                number_name = next((name for name, num in PHONE_NUMBERS.items() if num == number), number)
                f.write(f"  - {number_name} ({number}): {count} messages\n")
            
            f.write("\n## Key Evidence Categories\n\n")
            f.write(f"### Positive Relationships and Intentions\n\n")
            f.write(f"*{len(positive_relationship_evidence)} messages identified*\n\n")
            f.write("#### Top Evidence Examples:\n\n")
            
            # Write top 5 examples
            for i, evidence in enumerate(positive_relationship_evidence[:5], 1):
                f.write(f"**Example {i}:**\n")
                f.write(f"- **From:** {evidence['from_number']}\n")
                f.write(f"- **Date:** {evidence['timestamp']}\n")
                f.write(f"- **Message:** {evidence['message_text']}\n")
                f.write(f"- **Analysis:** {evidence['sentiment']}\n\n")
            
            f.write(f"### Parental Care and Love\n\n")
            f.write(f"*{len(parental_care_evidence)} messages identified*\n\n")
            f.write("#### Top Evidence Examples:\n\n")
            
            # Write top 5 examples
            for i, evidence in enumerate(parental_care_evidence[:5], 1):
                f.write(f"**Example {i}:**\n")
                f.write(f"- **From:** {evidence['from_number']}\n")
                f.write(f"- **Date:** {evidence['timestamp']}\n")
                f.write(f"- **Message:** {evidence['message_text']}\n")
                f.write(f"- **Analysis:** {evidence['sentiment']}\n\n")
            
            f.write(f"### Child Welfare Prioritization\n\n")
            f.write(f"*{len(child_welfare_evidence)} messages identified*\n\n")
            f.write("#### Top Evidence Examples:\n\n")
            
            # Write top 5 examples
            for i, evidence in enumerate(child_welfare_evidence[:5], 1):
                f.write(f"**Example {i}:**\n")
                f.write(f"- **From:** {evidence['from_number']}\n")
                f.write(f"- **Date:** {evidence['timestamp']}\n")
                f.write(f"- **Message:** {evidence['message_text']}\n")
                f.write(f"- **Analysis:** {evidence['sentiment']}\n\n")
            
            f.write("## Recommendations for Legal Team\n\n")
            f.write("1. **Focus on temporal patterns:** Review the full dataset to identify consistent patterns of positive behavior over time.\n")
            f.write("2. **Context is critical:** Consider the context of these messages within the broader case timeline.\n")
            f.write("3. **Cross-reference with other evidence:** These messages should be considered alongside other forms of evidence.\n")
            f.write("4. **Follow up interviews:** Consider interviewing the individuals identified in particularly positive exchanges.\n\n")
            
            f.write("---\n\n")
            f.write("*This report is confidential and intended solely for use by Tia's legal defense team.*\n")
        
        logger.info(f"Generated summary report: {SUMMARY_FILE}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        return False

# Main function
def main():
    """Main function to run the sentiment analysis"""
    logger.info("Starting sentiment analysis")
    
    # Print script information
    print("Sentiment Analysis for Legal Evidence")
    print("====================================")
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Summary report: {SUMMARY_FILE}")
    print("Starting analysis...")
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Input file not found: {INPUT_FILE}")
        print(f"Error: Input file not found: {INPUT_FILE}")
        return 1
    
    try:
        # Initialize OpenAI API
        init_openai()
        
        # Load input data
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            messages = list(reader)
        
        logger.info(f"Loaded {len(messages)} messages from {INPUT_FILE}")
        
        # Process messages
        results = process_messages(
            messages, 
            batch_size=BATCH_CONFIG["batch_size"],
            max_retries=BATCH_CONFIG["max_retries"]
        )
        
        # Save results
        if results:
            success = save_results_to_csv(results)
            if success:
                print(f"Successfully saved {len(results)} analyzed messages to {OUTPUT_FILE}")
            
            # Generate summary report
            summary_success = generate_summary_report(results)
            if summary_success:
                print(f"Generated summary report: {SUMMARY_FILE}")
        else:
            logger.warning("No results to save")
            print("Warning: No results were generated from the analysis")
        
        logger.info("Sentiment analysis completed")
        print("\nAnalysis completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

