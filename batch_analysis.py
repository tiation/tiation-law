#!/usr/bin/env python3
# batch_analysis.py
# Script to analyze messages in batches using OpenAI GPT-4

import os
import sys
import json
import time
import logging
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
INPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\input"
OUTPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\output"
BATCHES_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\batches"
RESULTS_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\results"
PROGRESS_FILE = os.path.join(BATCHES_DIR, "progress.json")
INPUT_FILE = os.path.join(INPUT_DIR, "tia_case_messages_cleaned.csv")
SENTIMENT_FILE = os.path.join(OUTPUT_DIR, "local_sentiment_results.csv")

# Create directories if they don't exist
for directory in [BATCHES_DIR, RESULTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Default batch settings
DEFAULT_BATCH_SIZE = 100
DEFAULT_MAX_DAILY_BATCHES = 5
DEFAULT_WAIT_TIME = 3  # seconds between API calls

class BatchAnalyzer:
    """Class to handle batch analysis of messages"""
    
    def __init__(self, batch_size=DEFAULT_BATCH_SIZE, max_daily_batches=DEFAULT_MAX_DAILY_BATCHES, 
                 wait_time=DEFAULT_WAIT_TIME, api_key=None, resume=True):
        """Initialize the batch analyzer"""
        self.batch_size = batch_size
        self.max_daily_batches = max_daily_batches
        self.wait_time = wait_time
        self.resume = resume
        
        # Load messages
        self.messages = self._load_messages()
        self.sentiment_data = self._load_sentiment_data()
        
        # Initialize OpenAI client
        self.client = self._init_openai(api_key)
        
        # Load or initialize progress
        self.progress = self._load_progress() if resume else self._init_progress()
        
        logger.info(f"BatchAnalyzer initialized with batch size: {batch_size}, max daily batches: {max_daily_batches}")
        logger.info(f"Loaded {len(self.messages)} messages and {len(self.sentiment_data)} sentiment results")
    
    def _load_messages(self):
        """Load messages from CSV file"""
        try:
            df = pd.read_csv(INPUT_FILE)
            logger.info(f"Loaded {len(df)} messages from {INPUT_FILE}")
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Failed to load messages: {e}")
            return []
    
    def _load_sentiment_data(self):
        """Load sentiment data from CSV file"""
        try:
            if os.path.exists(SENTIMENT_FILE):
                df = pd.read_csv(SENTIMENT_FILE)
                logger.info(f"Loaded {len(df)} sentiment results from {SENTIMENT_FILE}")
                return df.to_dict('records')
            else:
                logger.warning(f"Sentiment file not found: {SENTIMENT_FILE}")
                return []
        except Exception as e:
            logger.error(f"Failed to load sentiment data: {e}")
            return []
    
    def _init_openai(self, api_key=None):
        """Initialize OpenAI client"""
        try:
            # Load .env file
            load_dotenv()
            
            # Use provided key or load from .env
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                logger.error("OpenAI API key not found")
                return None
            
            client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    def _load_progress(self):
        """Load progress from file"""
        try:
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, 'r') as f:
                    progress = json.load(f)
                logger.info(f"Loaded progress: {progress['completed_batches']} completed batches, {len(progress['completed_message_ids'])} completed messages")
                return progress
            else:
                logger.info("No progress file found, initializing new progress")
                return self._init_progress()
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            return self._init_progress()
    
    def _init_progress(self):
        """Initialize progress data"""
        return {
            "start_time": datetime.now().isoformat(),
            "completed_batches": 0,
            "completed_message_ids": [],
            "failed_message_ids": [],
            "daily_counts": {},
            "last_batch_time": None
        }
    
    def _save_progress(self):
        """Save progress to file"""
        try:
            # Update last batch time
            self.progress["last_batch_time"] = datetime.now().isoformat()
            
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(self.progress, f, indent=2)
            logger.info(f"Progress saved: {self.progress['completed_batches']} completed batches")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def _update_daily_count(self):
        """Update the count of batches processed today"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.progress["daily_counts"]:
            self.progress["daily_counts"][today] = 0
        
        self.progress["daily_counts"][today] += 1
        logger.info(f"Daily count for {today}: {self.progress['daily_counts'][today]}")
    
    def _can_process_more_today(self):
        """Check if we can process more batches today"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.progress["daily_counts"]:
            return True
        
        return self.progress["daily_counts"][today] < self.max_daily_batches
    
    def _prioritize_messages(self):
        """Prioritize messages for analysis"""
        # Skip messages that have already been processed
        pending_messages = [m for m in self.messages 
                           if m.get('message_id') not in self.progress["completed_message_ids"] 
                           and m.get('message_id') not in self.progress["failed_message_ids"]]
        
        if not pending_messages:
            logger.info("No pending messages to process")
            return []
        
        logger.info(f"Prioritizing {len(pending_messages)} pending messages")
        
        # Match sentiment data to prioritize by sentiment strength
        for message in pending_messages:
            message_id = message.get('message_id')
            # Find matching sentiment data
            sentiment_match = next((s for s in self.sentiment_data 
                                   if s.get('message_id') == message_id), None)
            
            if sentiment_match:
                # Use sentiment compound score for priority
                message['sentiment_compound'] = float(sentiment_match.get('sentiment_compound', 0))
                
                # Add category flags for prioritization
                message['is_positive_relationship'] = sentiment_match.get('positive_relationship', False)
                message['is_parental_care'] = sentiment_match.get('parental_care', False)
                message['is_child_welfare'] = sentiment_match.get('child_welfare', False)
            else:
                # Default values if no sentiment data
                message['sentiment_compound'] = 0
                message['is_positive_relationship'] = False
                message['is_parental_care'] = False
                message['is_child_welfare'] = False
        
        # Calculate priority score:
        # 1. Higher absolute sentiment score (both positive and negative are interesting)
        # 2. Messages in multiple categories are more important
        # 3. Add a small random factor to avoid processing messages in same order every time
        for message in pending_messages:
            category_count = sum([
                1 if message.get('is_positive_relationship') else 0,
                1 if message.get('is_parental_care') else 0,
                1 if message.get('is_child_welfare') else 0
            ])
            
            # Priority formula: absolute sentiment + category bonus + small random factor
            message['priority_score'] = (
                abs(message.get('sentiment_compound', 0)) +  # Absolute sentiment score
                (category_count * 0.2) +  # Bonus for being in multiple categories
                (random.random() * 0.1)  # Small random factor (0-0.1)
            )
        
        # Sort by priority score (descending)
        sorted_messages = sorted(pending_messages, key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return sorted_messages
    
    def _create_batch(self):
        """Create a batch of messages for processing"""
        prioritized_messages = self._prioritize_messages()
        
        if not prioritized_messages:
            return None
        
        # Take the top N messages
        batch = prioritized_messages[:self.batch_size]
        
        # Create batch metadata
        batch_metadata = {
            "batch_id": f"batch_{self.progress['completed_batches'] + 1}",
            "created_at": datetime.now().isoformat(),
            "message_count": len(batch),
            "message_ids": [m.get('message_id') for m in batch]
        }
        
        # Save batch to file
        batch_file = os.path.join(BATCHES_DIR, f"{batch_metadata['batch_id']}.json")
        try:
            with open(batch_file, 'w') as f:
                json.dump({
                    "metadata": batch_metadata,
                    "messages": batch
                }, f, indent=2)
            logger.info(f"Created batch {batch_metadata['batch_id']} with {len(batch)} messages")
            return batch_metadata
        except Exception as e:
            logger.error(f"Failed to save batch: {e}")
            return None
    
    def _analyze_message(self, message):
        """Analyze a single message with GPT-4"""
        if not self.client:
            logger.error("OpenAI client not initialized")
            return None
        
        try:
            # Prepare prompt for GPT-4
            prompt = f"""
            Please analyze this text message for evidence that might be helpful in a legal defense case.
            Focus on identifying:
            1. Evidence of positive relationships and good intentions
            2. Signs of parental love, care, and responsibility
            3. Indications of child welfare prioritization
            4. Context that might explain statements or actions

            MESSAGE DETAILS:
            Date: {message.get('timestamp', 'Unknown')}
            From: {message.get('from_number', 'Unknown')}
            Direction: {message.get('direction', 'Unknown')}

            MESSAGE TEXT:
            "{message.get('message_text', '')}"

            Please provide:
            1. A brief sentiment analysis
            2. Key evidence points
            3. How this could support the defense
            4. Any context that should be considered
            """
            
            # Call GPT-4 API
            logger.info(f"Calling GPT-4 API for message {message.get('message_id')}")
            
            # Wait to avoid rate limiting
            time.sleep(self.wait_time)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a legal analyst helping a defense team identify positive evidence."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content
            
            # Create result
            result = {
                "message_id": message.get('message_id'),
                "timestamp": message.get('timestamp'),
                "from_number": message.get('from_number'),
                "direction": message.get('direction'),
                "message_text": message.get('message_text'),
                "gpt4_analysis": analysis,
                "analyzed_at": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze message {message.get('message_id')}: {e}")
            return None
    
    def process_batch(self, batch_id):
        """Process a specific batch of messages"""
        batch_file = os.path.join(BATCHES_DIR, f"{batch_id}.json")
        
        if not os.path.exists(batch_file):
            logger.error(f"Batch file not found: {batch_file}")
            return False
        
        # Load batch
        try:
            with open(batch_file, 'r') as f:
                batch_data = json.load(f)
            
            metadata = batch_data.get("metadata", {})
            messages = batch_data.get("messages", [])
            
            logger.info(f"Processing batch {batch_id} with {len(messages)} messages")
            
            # Process each message
            results = []
            for i, message in enumerate(messages, 1):
                try:
                    logger.info(f"Processing message {i}/{len(messages)} in batch {batch_id}")
                    result = self._analyze_message(message)
                    
                    if result:
                        results.append(result)
                        # Add to completed messages
                        self.progress["completed_message_ids"].append(message.get('message_id'))
                    else:
                        # Add to failed messages
                        self.progress["failed_message_ids"].append(message.get('message_id'))
                    
                    # Save progress periodically
                    if i % 5 == 0:
                        self._save_progress()
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    self.progress["failed_message_ids"].append(message.get('message_id'))
            
            # Save results
            if results:
                results_file = os.path.join(RESULTS_DIR, f"{batch_id}_results.json")
                with open(results_file, 'w') as f:
                    json.dump({
                        "batch_id": batch_id,
                        "processed_at": datetime.now().isoformat(),
                        "results": results
                    }, f, indent=2)
                logger.info(f"Saved {len(results)} results to {results_file}")
            
            # Update progress
            self.progress["completed_batches"] += 1
            self._update_daily_count()
            self._save_progress()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process batch {batch_id}: {e}")
            return False
    
    def run(self):
        """Run the batch analyzer"""
        if not self.client:
            logger.error("OpenAI client not initialized, aborting")
            return False
        
        # Check if we can process more batches today
        if not self._can_process_more_today():
            logger.warning(f"Daily limit of {self.max_daily_batches} batches reached, skipping")
            return False
        
        # Create and process a new batch
        batch_metadata = self._create_batch()
        
        if not batch_metadata:
            logger.info("No more messages to process")
            return False
        
        batch_id = batch_metadata.get("batch_id")
        success = self.process_batch(batch_id)
        
        if success:
            logger.info(f"Successfully processed batch {batch_id}")
        else:
            logger.error(f"Failed to process batch {batch_id}")
        
        return success
    
    def combine_results(self):
        """Combine all batch results into a single file"""
        results = []
        
        # Find all result files
        result_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith("_results.json")]
        
        if not result_files:
            logger.warning("No result files found")
            return False
        
        # Load all results
        for file in result_files:
            try:
                with open(os.path.join(RESULTS_DIR, file), 'r') as f:
                    batch_results = json.load(f)
                
                results.extend(batch_results.get("results", []))
                logger.info(f"Loaded {len(batch_results.get('results', []))} results from {file}")
            except Exception as e:
                logger.error(f"Failed to load results from {file}: {e}")
        
        if not results:
            logger.warning("No results to combine")
            return False
        
        # Save combined results
        combined_file = os.path.join(OUTPUT_DIR, "gpt4_analysis_results.json")
        try:
            with open(combined_file, 'w') as f:
                json.dump({
                    "generated_at": datetime.now().isoformat(),
                    "total_messages": len(results),
                    "results": results
                }, f, indent=2)
            logger.info(f"Combined {len(results)} results to {combined_file}")
            
            # Also save as CSV for easier analysis
            csv_file = os.path.join(OUTPUT_DIR, "gpt4_analysis_results.csv")
            df = pd.json_normalize(results)
            df.to_csv(csv_file, index=False)
            logger.info(f"Saved CSV to {csv_file}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to save combined results: {e}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Process messages in batches using GPT-4")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
                        help=f"Number of messages per batch (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--max-daily-batches", type=int, default=DEFAULT_MAX_DAILY_BATCHES,
                        help=f"Maximum number of batches to process per day (default: {DEFAULT_MAX_DAILY_BATCHES})")
    parser.add_argument("--wait-time", type=float, default=DEFAULT_WAIT_TIME,
                        help=f"Time to wait between API calls in seconds (default: {DEFAULT_WAIT_TIME})")
    parser.add_argument("--no-resume", action="store_true",
                        help="Do not resume from previous progress")
    parser.add_argument("--combine-only", action="store_true",
                        help="Only combine existing results without processing new batches")
    parser.add_argument("--api-key", type=str, default=None,
                        help="OpenAI API key (if not provided, will use .env file)")
    parser.add_argument("--process-batch", type=str, default=None,
                        help="Process a specific batch by ID (e.g., batch_1)")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = BatchAnalyzer(
        batch_size=args.batch_size,
        max_daily_batches=args.max_daily_batches,
        wait_time=args.wait_time,
        api_key=args.api_key,
        resume=not args.no_resume
    )
    
    # Process specific batch if requested
    if args.process_batch:
        logger.info(f"Processing specific batch: {args.process_batch}")
        success = analyzer.process_batch(args.process_batch)
        if success:
            logger.info(f"Successfully processed batch {args.process_batch}")
        else:
            logger.error(f"Failed to process batch {args.process_batch}")
        return 0 if success else 1
    
    # Only combine results if requested
    if args.combine_only:
        logger.info("Combining existing results")
        success = analyzer.combine_results()
        if success:
            logger.info("Successfully combined results")
        else:
            logger.error("Failed to combine results")
        return 0 if success else 1
    
    # Run normal batch processing
    success = analyzer.run()
    
    # Always try to combine results
    combine_success = analyzer.combine_results()
    
    if success:
        logger.info("Successfully processed batch")
    else:
        logger.warning("Batch processing completed with issues")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

