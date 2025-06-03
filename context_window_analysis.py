#!/usr/bin/env python3
# context_window_analysis.py
# Script to analyze messages in chunks suitable for AI context windows

import os
import sys
import json
import csv
import logging
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('context_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
INPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\input"
OUTPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\output"
CHUNKS_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\chunks"
CONTEXT_RESULTS_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\context_results"
SENTIMENT_FILE = os.path.join(OUTPUT_DIR, "local_sentiment_results.csv")
INPUT_FILE = os.path.join(INPUT_DIR, "tia_case_messages_cleaned.csv")

# Create directories if they don't exist
for directory in [CHUNKS_DIR, CONTEXT_RESULTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Analysis categories - these must match the column names in the CSV exactly
CATEGORIES = {
    "positive_relationship": {  # Matches the CSV column name (singular)
        "name": "Positive Relationships",
        "indicators": ["love", "care", "trust", "respect", "support", "help", "appreciate", "thank", "sorry", "good"],
        "output_file": "positive_relationships_analysis.md"
    },
    "parental_care": {
        "name": "Parental Care",
        "indicators": ["child", "children", "kid", "kids", "parent", "family", "protect", "safe", "school", "proud"],
        "output_file": "parental_care_analysis.md"
    },
    "child_welfare": {
        "name": "Child Welfare",
        "indicators": ["safe", "welfare", "wellbeing", "health", "care", "protect", "support", "need", "help", "love"],
        "output_file": "child_welfare_analysis.md"
    }
}

# Default chunk settings
DEFAULT_CHUNK_SIZE = 50
DEFAULT_TOP_MESSAGES = 5
DEFAULT_ASSISTANT_PROMPT = """
You are analyzing text messages for evidence that could support a legal defense case.
Focus specifically on identifying evidence of {category_name}.

Look for messages that demonstrate:
{indicators}

For each message, provide:
1. A brief assessment of how it shows {category_name}
2. Key phrases or words that serve as evidence
3. How this could support the defense case

IMPORTANT: Focus ONLY on {category_name} in your analysis.
"""

class ContextWindowAnalyzer:
    """Class to handle message analysis in chunks for AI context windows"""
    
    def __init__(self, chunk_size=DEFAULT_CHUNK_SIZE, top_messages=DEFAULT_TOP_MESSAGES, 
                 assistant_prompt=DEFAULT_ASSISTANT_PROMPT):
        """Initialize the context window analyzer"""
        self.chunk_size = chunk_size
        self.top_messages = top_messages
        self.assistant_prompt = assistant_prompt
        
        # Load messages and sentiment data
        self.messages = self._load_messages()
        self.sentiment_data = self._load_sentiment_data()
        
        logger.info(f"ContextWindowAnalyzer initialized with chunk size: {chunk_size}")
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
                # Load CSV with explicit boolean type conversion
                df = pd.read_csv(SENTIMENT_FILE)
                
                # Convert boolean columns from string to actual boolean values
                boolean_columns = ['positive_relationship', 'parental_care', 'child_welfare']
                for col in boolean_columns:
                    if col in df.columns:
                        # Convert True/False strings to actual booleans
                        df[col] = df[col].map({'True': True, 'False': False})
                
                logger.info(f"Loaded {len(df)} sentiment results from {SENTIMENT_FILE}")
                
                # Log column names for debugging
                logger.debug(f"Sentiment data columns: {list(df.columns)}")
                
                # Count True values in each category for verification
                for col in boolean_columns:
                    if col in df.columns:
                        true_count = df[col].sum()
                        logger.info(f"Found {true_count} True values in column '{col}'")
                
                return df.to_dict('records')
            else:
                logger.warning(f"Sentiment file not found: {SENTIMENT_FILE}")
                return []
        except Exception as e:
            logger.error(f"Failed to load sentiment data: {e}")
            return []
    
    def _filter_messages_by_category(self, category):
        """Filter messages by category and sentiment"""
        # The category column name in the CSV is exactly the same as the category name
        category_col = category
        
        # Track filter stats
        total_messages = len(self.messages)
        matched_sentiment_count = 0
        category_match_count = 0
        
        # Filter messages by sentiment data
        filtered_messages = []
        
        for message in self.messages:
            message_id = message.get('message_id')
            
            # Find matching sentiment data
            sentiment_match = next((s for s in self.sentiment_data if s.get('message_id') == message_id), None)
            
            if sentiment_match:
                matched_sentiment_count += 1
                
                # Check if message belongs to this category
                # Note: We need to handle various potential formats (boolean, string, etc.)
                is_in_category = sentiment_match.get(category_col, False)
                
                # Convert string 'True'/'False' to boolean if needed
                if isinstance(is_in_category, str):
                    is_in_category = is_in_category.lower() == 'true'
                
                if is_in_category:
                    category_match_count += 1
                    
                    # Add sentiment data to message
                    message['sentiment_compound'] = float(sentiment_match.get('sentiment_compound', 0))
                    message['sentiment_category'] = sentiment_match.get('sentiment_category', '')
                    
                    # Add keywords if available
                    keywords_field = f"{category}_keywords"
                    if keywords_field in sentiment_match:
                        # Handle None or empty values
                        if sentiment_match[keywords_field] and not pd.isna(sentiment_match[keywords_field]):
                            message['keywords'] = sentiment_match[keywords_field]
                    
                    filtered_messages.append(message)
        
        # Sort by sentiment strength (positive messages first)
        sorted_messages = sorted(filtered_messages, key=lambda x: float(x.get('sentiment_compound', 0)), reverse=True)
        
        # Log detailed filtering stats
        logger.info(f"Filtering stats for '{category}':")
        logger.info(f"  - Total messages: {total_messages}")
        logger.info(f"  - Messages with sentiment data: {matched_sentiment_count}")
        logger.info(f"  - Messages in category '{category}': {category_match_count}")
        logger.info(f"  - Final filtered count: {len(sorted_messages)}")
        
        return sorted_messages
    
    def _create_chunks(self, messages, category):
        """Create chunks of messages for analysis"""
        chunks = []
        
        # Split messages into chunks
        for i in range(0, len(messages), self.chunk_size):
            chunk = messages[i:i + self.chunk_size]
            chunk_id = f"{category}_chunk_{i//self.chunk_size + 1}"
            
            chunks.append({
                "chunk_id": chunk_id,
                "start_index": i,
                "end_index": i + len(chunk) - 1,
                "messages": chunk
            })
        
        logger.info(f"Created {len(chunks)} chunks for category {category}")
        return chunks
    
    def _save_chunk(self, chunk, category):
        """Save a chunk to a file"""
        chunk_file = os.path.join(CHUNKS_DIR, f"{chunk['chunk_id']}.json")
        
        try:
            with open(chunk_file, 'w') as f:
                json.dump({
                    "chunk_id": chunk['chunk_id'],
                    "category": category,
                    "created_at": datetime.now().isoformat(),
                    "start_index": chunk['start_index'],
                    "end_index": chunk['end_index'],
                    "message_count": len(chunk['messages']),
                    "messages": chunk['messages']
                }, f, indent=2)
            
            logger.info(f"Saved chunk {chunk['chunk_id']} with {len(chunk['messages'])} messages")
            return chunk_file
        except Exception as e:
            logger.error(f"Failed to save chunk: {e}")
            return None
    
    def _format_messages_for_prompt(self, messages):
        """Format messages for inclusion in a prompt"""
        formatted = []
        
        for i, message in enumerate(messages, 1):
            formatted.append(f"--- MESSAGE {i} ---")
            formatted.append(f"Date: {message.get('timestamp', 'Unknown')}")
            formatted.append(f"From: {message.get('from_number', 'Unknown')}")
            formatted.append(f"Direction: {message.get('direction', 'Unknown')}")
            formatted.append(f"Sentiment: {message.get('sentiment_category', 'Unknown')} (score: {float(message.get('sentiment_compound', 0)):.2f})")
            
            if message.get('keywords'):
                formatted.append(f"Keywords: {message.get('keywords', '')}")
            
            formatted.append(f"Text: {message.get('message_text', '')}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _create_prompt_for_chunk(self, chunk, category):
        """Create a prompt for analyzing a chunk of messages"""
        category_info = CATEGORIES[category]
        
        # Format indicators as bullet points
        indicators_text = "\n".join([f"- Evidence of {indicator}" for indicator in category_info['indicators']])
        
        # Create the prompt
        prompt = self.assistant_prompt.format(
            category_name=category_info['name'],
            indicators=indicators_text
        )
        
        # Add the messages
        prompt += "\n\nHere are the messages to analyze:\n\n"
        prompt += self._format_messages_for_prompt(chunk['messages'])
        
        return prompt
    
    def _call_ai_assistant(self, prompt, category, chunk_id):
        """Call AI assistant to analyze messages"""
        # For this implementation, we'll output the prompt to a file
        # and instruct the user how to process it
        prompt_file = os.path.join(CHUNKS_DIR, f"{chunk_id}_prompt.txt")
        
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            logger.info(f"Saved prompt to {prompt_file}")
            
            # Create placeholder for manual analysis
            result_file = os.path.join(CONTEXT_RESULTS_DIR, f"{chunk_id}_result.md")
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"# Analysis of {CATEGORIES[category]['name']} - Chunk {chunk_id}\n\n")
                f.write(f"*This file contains analysis results for {len(chunk['messages'])} messages.*\n\n")
                f.write("## Instructions\n\n")
                f.write(f"1. Review the prompt in: {prompt_file}\n")
                f.write("2. Analyze the messages focusing on the specified category\n")
                f.write("3. Replace this content with your analysis\n\n")
                f.write("## Placeholder Analysis\n\n")
                f.write("*This is a placeholder. Replace with actual analysis.*\n\n")
                
                # Add message previews
                f.write("## Messages in this Chunk\n\n")
                for i, message in enumerate(chunk['messages'][:10], 1):
                    f.write(f"### Message {i}\n\n")
                    f.write(f"**Date:** {message.get('timestamp', 'Unknown')}\n\n")
                    f.write(f"**Text:** {message.get('message_text', '')[:100]}...\n\n")
            
            logger.info(f"Created result placeholder at {result_file}")
            return result_file
            
        except Exception as e:
            logger.error(f"Error in AI assistant call: {e}")
            return None
    
    def _extract_top_messages(self, category, count=None):
        """Extract top messages from a category for summary"""
        if count is None:
            count = self.top_messages
        
        # Filter messages by category
        messages = self._filter_messages_by_category(category)
        
        # Take top N messages
        top_messages = messages[:count]
        
        return top_messages
    
    def _create_category_summary(self, category):
        """Create a summary for a category"""
        category_info = CATEGORIES[category]
        top_messages = self._extract_top_messages(category)
        
        # Create summary file
        summary_file = os.path.join(CONTEXT_RESULTS_DIR, category_info['output_file'])
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"# {category_info['name']} Analysis\n\n")
                f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                
                # Overview
                messages = self._filter_messages_by_category(category)
                f.write(f"## Overview\n\n")
                f.write(f"- **Total messages analyzed:** {len(messages)}\n")
                f.write(f"- **Top indicators:** {', '.join(category_info['indicators'])}\n\n")
                
                # Top messages
                f.write(f"## Top {len(top_messages)} Messages\n\n")
                for i, message in enumerate(top_messages, 1):
                    f.write(f"### Message {i}\n\n")
                    f.write(f"**Date:** {message.get('timestamp', 'Unknown')}\n")
                    f.write(f"**From:** {message.get('from_number', 'Unknown')}\n")
                    f.write(f"**Direction:** {message.get('direction', 'Unknown')}\n")
                    f.write(f"**Sentiment:** {message.get('sentiment_category', 'Unknown')} (score: {float(message.get('sentiment_compound', 0)):.2f})\n")
                    
                    if message.get('keywords'):
                        f.write(f"**Keywords:** {message.get('keywords', '')}\n")
                    
                    f.write(f"\n**Message Text:**\n```\n{message.get('message_text', '')}\n```\n\n")
                    f.write("---\n\n")
                
                # Chunks
                chunks = self._create_chunks(messages, category)
                f.write(f"## Analysis Chunks\n\n")
                f.write(f"The messages have been divided into {len(chunks)} chunks for detailed analysis.\n\n")
                
                for i, chunk in enumerate(chunks, 1):
                    chunk_id = chunk['chunk_id']
                    result_file = f"{chunk_id}_result.md"
                    if os.path.exists(os.path.join(CONTEXT_RESULTS_DIR, result_file)):
                        f.write(f"- [Chunk {i}: Messages {chunk['start_index']+1}-{chunk['end_index']+1}]({result_file})\n")
                    else:
                        f.write(f"- Chunk {i}: Messages {chunk['start_index']+1}-{chunk['end_index']+1} (analysis pending)\n")
                
                f.write("\n## Next Steps\n\n")
                f.write("1. Review each chunk's detailed analysis\n")
                f.write("2. Consolidate findings across chunks\n")
                f.write("3. Identify patterns and recurring themes\n")
                f.write("4. Incorporate insights into legal defense strategy\n\n")
                
                f.write("---\n\n")
                f.write(f"*This analysis focuses specifically on {category_info['name'].lower()} evidence for Tia's legal defense.*\n")
            
            logger.info(f"Created category summary at {summary_file}")
            return summary_file
            
        except Exception as e:
            logger.error(f"Error creating category summary: {e}")
            return None
    
    def process_category(self, category):
        """Process all messages for a specific category"""
        if category not in CATEGORIES:
            logger.error(f"Unknown category: {category}")
            return False
        
        logger.info(f"Processing category: {category}")
        
        # Filter messages by category
        messages = self._filter_messages_by_category(category)
        
        if not messages:
            logger.warning(f"No messages found for category {category}")
            return False
        
        # Create chunks
        chunks = self._create_chunks(messages, category)
        
        # Process each chunk
        for chunk in chunks:
            # Save chunk to file
            chunk_file = self._save_chunk(chunk, category)
            
            if chunk_file:
                # Create prompt for analysis
                prompt = self._create_prompt_for_chunk(chunk, category)
                
                # Call AI assistant
                result_file = self._call_ai_assistant(prompt, category, chunk['chunk_id'])
                
                if not result_file:
                    logger.warning(f"Failed to process chunk {chunk['chunk_id']}")
        
        # Create category summary
        summary_file = self._create_category_summary(category)
        
        return True
    
    def create_main_index(self):
        """Create a main index file for all analyses"""
        index_file = os.path.join(CONTEXT_RESULTS_DIR, "index.md")
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write("# Message Analysis for Legal Defense\n\n")
                f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                
                f.write("## Analysis Categories\n\n")
                
                for category, info in CATEGORIES.items():
                    output_file = info['output_file']
                    if os.path.exists(os.path.join(CONTEXT_RESULTS_DIR, output_file)):
                        f.write(f"- [{info['name']}]({output_file})\n")
                    else:
                        f.write(f"- {info['name']} (analysis pending)\n")
                
                f.write("\n## Analysis Process\n\n")
                f.write("The analysis has been broken down into manageable chunks to fit within context windows:\n\n")
                f.write("1. Messages are filtered by category based on initial sentiment analysis\n")
                f.write("2. Each category is divided into chunks of 50 messages\n")
                f.write("3. Each chunk is analyzed separately, focusing on specific evidence types\n")
                f.write("4. Results are combined into category summaries\n\n")
                
                f.write("## Summary of Findings\n\n")
                f.write("### Positive Relationships\n\n")
                positive_count = len(self._filter_messages_by_category("positive_relationship"))
                f.write(f"- {positive_count} messages showing evidence of positive relationships\n")
                f.write("- Key indicators include expressions of love, care, trust, and respect\n\n")
                
                f.write("### Parental Care\n\n")
                parental_count = len(self._filter_messages_by_category("parental_care"))
                f.write(f"- {parental_count} messages demonstrating parental care and responsibility\n")
                f.write("- Key indicators include child welfare, family focus, and protective behaviors\n\n")
                
                f.write("### Child Welfare\n\n")
                welfare_count = len(self._filter_messages_by_category("child_welfare"))
                f.write(f"- {welfare_count} messages highlighting child welfare prioritization\n")
                f.write("- Key indicators include safety concerns, wellbeing focus, and supportive actions\n\n")
                
                f.write("## Next Steps\n\n")
                f.write("1. Review individual category analyses\n")
                f.write("2. Identify strongest evidence pieces for legal defense\n")
                f.write("3. Develop timeline of positive behaviors and intentions\n")
                f.write("4. Prepare witness preparation based on message evidence\n\n")
                
                f.write("---\n\n")
                f.write("*This analysis is confidential and intended solely for use by Tia's legal defense team.*\n")
            
            logger.info(f"Created main index at {index_file}")
            return index_file
            
        except Exception as e:
            logger.error(f"Error creating main index: {e}")
            return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Process messages in chunks for AI context windows")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"Number of messages per chunk (default: {DEFAULT_CHUNK_SIZE})")
    parser.add_argument("--top-messages", type=int, default=DEFAULT_TOP_MESSAGES,
                        help=f"Number of top messages to highlight (default: {DEFAULT_TOP_MESSAGES})")
    parser.add_argument("--category", type=str, choices=list(CATEGORIES.keys()),
                        help="Process only a specific category")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        # Also set the file handler to DEBUG
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Initialize analyzer
    analyzer = ContextWindowAnalyzer(
        chunk_size=args.chunk_size,
        top_messages=args.top_messages
    )
    
    # Process specific category if requested
    if args.category:
        logger.info(f"Processing only category: {args.category}")
        success = analyzer.process_category(args.category)
        if success:
            logger.info(f"Successfully processed category {args.category}")
        else:
            logger.error(f"Failed to process category {args.category}")
    else:
        # Process all categories
        logger.info("Processing all categories")
        for category in CATEGORIES:
            success = analyzer.process_category(category)
            if success:
                logger.info(f"Successfully processed category {category}")
            else:
                logger.error(f"Failed to process category {category}")
    
    # Create main index
    analyzer.create_main_index()
    
    logger.info("Analysis completed")
    print("\nAnalysis completed. Results are available in the context_results directory.")
    print(f"Main index: {os.path.join(CONTEXT_RESULTS_DIR, 'index.md')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

