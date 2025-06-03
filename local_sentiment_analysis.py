#!/usr/bin/env python3
# local_sentiment_analysis.py
# Script to analyze messages using local NLTK VADER sentiment analyzer

import os
import sys
import csv
import re
import logging
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('local_sentiment_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
INPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\input"
OUTPUT_DIR = r"C:\Users\admin\Documents\sentiment_analysis\data\output"
INPUT_FILE = os.path.join(INPUT_DIR, "tia_case_messages_cleaned.csv")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "local_sentiment_results.csv")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "local_sentiment_summary.md")

# Ensure NLTK resources are available
def setup_nltk():
    """Download required NLTK resources"""
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        print("Downloading NLTK VADER lexicon...")
        nltk.download('vader_lexicon')
    
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK tokenizer...")
        nltk.download('punkt')

# Keyword lists for specific categories
POSITIVE_RELATIONSHIP_KEYWORDS = [
    'love', 'care', 'trust', 'respect', 'support', 'help', 
    'together', 'friend', 'happy', 'appreciate', 'thank', 
    'grateful', 'sorry', 'please', 'kindness', 'understand',
    'listen', 'positive', 'good', 'better', 'best', 'well',
    'calm', 'peaceful', 'hope', 'wish', 'future', 'miss'
]

PARENTAL_CARE_KEYWORDS = [
    'child', 'children', 'kid', 'kids', 'son', 'daughter', 
    'parent', 'mom', 'mum', 'dad', 'father', 'mother', 'family',
    'love', 'care', 'protect', 'safe', 'school', 'homework', 
    'bedtime', 'sleep', 'eat', 'food', 'dinner', 'lunch',
    'doctor', 'health', 'well', 'sick', 'medicine', 'hug',
    'proud', 'grow', 'play', 'teach', 'learn', 'future',
    'birthday', 'present', 'gift', 'holiday', 'weekend'
]

CHILD_WELFARE_KEYWORDS = [
    'safe', 'safety', 'protect', 'protection', 'secure', 'welfare',
    'wellbeing', 'well-being', 'health', 'healthy', 'doctor', 'medical',
    'school', 'education', 'learn', 'teacher', 'homework', 'study',
    'happy', 'happiness', 'comfort', 'comfortable', 'future', 'grow',
    'development', 'routine', 'schedule', 'sleep', 'rest', 'food',
    'eat', 'nutrition', 'care', 'love', 'support', 'help', 'need'
]

# Analyze sentiment with VADER
def analyze_sentiment(text):
    """Analyze sentiment of text using VADER"""
    if not text or text.strip() == '':
        return {
            'compound': 0,
            'pos': 0,
            'neu': 0,
            'neg': 0,
            'sentiment_category': 'neutral'
        }
    
    sid = SentimentIntensityAnalyzer()
    sentiment_scores = sid.polarity_scores(text)
    
    # Determine sentiment category
    compound = sentiment_scores['compound']
    if compound >= 0.05:
        sentiment_category = 'positive'
    elif compound <= -0.05:
        sentiment_category = 'negative'
    else:
        sentiment_category = 'neutral'
    
    return {
        'compound': compound,
        'pos': sentiment_scores['pos'],
        'neu': sentiment_scores['neu'],
        'neg': sentiment_scores['neg'],
        'sentiment_category': sentiment_category
    }

# Check for keywords
def check_keywords(text, keyword_list):
    """Check if text contains any keywords from the list"""
    if not text or text.strip() == '':
        return False, []
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in keyword_list:
        # Look for whole word matches using regex word boundaries
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            found_keywords.append(keyword)
    
    return len(found_keywords) > 0, found_keywords

# Generate keyword-based insights
def generate_insights(text):
    """Generate insights based on keyword matches"""
    insights = []
    
    # Check for positive relationship indicators
    has_positive_rel, positive_rel_keywords = check_keywords(text, POSITIVE_RELATIONSHIP_KEYWORDS)
    if has_positive_rel:
        insights.append(f"Positive relationship indicators: {', '.join(positive_rel_keywords)}")
    
    # Check for parental care indicators
    has_parental_care, parental_care_keywords = check_keywords(text, PARENTAL_CARE_KEYWORDS)
    if has_parental_care:
        insights.append(f"Parental care indicators: {', '.join(parental_care_keywords)}")
    
    # Check for child welfare indicators
    has_child_welfare, child_welfare_keywords = check_keywords(text, CHILD_WELFARE_KEYWORDS)
    if has_child_welfare:
        insights.append(f"Child welfare indicators: {', '.join(child_welfare_keywords)}")
    
    return "; ".join(insights)

# Process messages
def process_messages(messages):
    """Process messages with local sentiment analysis"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Track sentiment stats by phone number
    sentiment_by_number = defaultdict(lambda: {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0})
    keyword_by_number = defaultdict(lambda: {
        'positive_relationship': 0, 
        'parental_care': 0, 
        'child_welfare': 0
    })
    
    # Process messages
    results = []
    for i, message in enumerate(messages):
        # Skip empty messages
        if not message['message_text'] or message['message_text'].strip() == '':
            continue
        
        # Get basic message details
        message_id = message['message_id']
        timestamp = message['timestamp']
        from_number = message['from_number']
        direction = message['direction']
        message_text = message['message_text']
        
        # Analyze sentiment
        sentiment = analyze_sentiment(message_text)
        
        # Check keywords
        has_positive_rel, positive_rel_keywords = check_keywords(message_text, POSITIVE_RELATIONSHIP_KEYWORDS)
        has_parental_care, parental_care_keywords = check_keywords(message_text, PARENTAL_CARE_KEYWORDS)
        has_child_welfare, child_welfare_keywords = check_keywords(message_text, CHILD_WELFARE_KEYWORDS)
        
        # Generate insights
        insights = generate_insights(message_text)
        
        # Determine evidence categories
        evidence_categories = []
        if has_positive_rel:
            evidence_categories.append("Positive Relationships")
        if has_parental_care:
            evidence_categories.append("Parental Care")
        if has_child_welfare:
            evidence_categories.append("Child Welfare")
        
        # Update sentiment stats
        sentiment_by_number[from_number]['total'] += 1
        sentiment_by_number[from_number][sentiment['sentiment_category']] += 1
        
        # Update keyword stats
        if has_positive_rel:
            keyword_by_number[from_number]['positive_relationship'] += 1
        if has_parental_care:
            keyword_by_number[from_number]['parental_care'] += 1
        if has_child_welfare:
            keyword_by_number[from_number]['child_welfare'] += 1
        
        # Create result entry
        result = {
            'message_id': message_id,
            'timestamp': timestamp,
            'from_number': from_number,
            'direction': direction,
            'message_text': message_text,
            'sentiment_compound': sentiment['compound'],
            'sentiment_category': sentiment['sentiment_category'],
            'positive_relationship': has_positive_rel,
            'parental_care': has_parental_care,
            'child_welfare': has_child_welfare,
            'positive_relationship_keywords': ','.join(positive_rel_keywords),
            'parental_care_keywords': ','.join(parental_care_keywords),
            'child_welfare_keywords': ','.join(child_welfare_keywords),
            'insights': insights,
            'evidence_categories': ','.join(evidence_categories)
        }
        
        results.append(result)
        
        # Log progress
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1} messages")
    
    logger.info(f"Completed processing {len(results)} messages")
    return results, sentiment_by_number, keyword_by_number

# Save results to CSV
def save_results_to_csv(results):
    """Save analysis results to CSV file"""
    if not results:
        logger.warning("No results to save")
        return False
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Write to CSV
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        logger.info(f"Saved {len(results)} results to {OUTPUT_FILE}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return False

# Generate summary report
def generate_summary_report(results, sentiment_by_number, keyword_by_number):
    """Generate summary report highlighting key evidence"""
    if not results:
        logger.warning("No results to summarize")
        return False
    
    try:
        # Prepare evidence examples by category
        positive_relationship_evidence = [r for r in results if r['positive_relationship']]
        parental_care_evidence = [r for r in results if r['parental_care']]
        child_welfare_evidence = [r for r in results if r['child_welfare']]
        
        # Sort by sentiment strength
        positive_relationship_evidence.sort(key=lambda x: x['sentiment_compound'], reverse=True)
        parental_care_evidence.sort(key=lambda x: x['sentiment_compound'], reverse=True)
        child_welfare_evidence.sort(key=lambda x: x['sentiment_compound'], reverse=True)
        
        # Generate report
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            f.write("# Local Sentiment Analysis Summary Report\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## Overview\n\n")
            f.write(f"- **Total messages analyzed:** {len(results)}\n")
            f.write(f"- **Messages by phone number:**\n")
            
            for number, stats in sentiment_by_number.items():
                positive_pct = (stats['positive'] / stats['total'] * 100) if stats['total'] > 0 else 0
                f.write(f"  - {number}: {stats['total']} messages ({stats['positive']} positive, {positive_pct:.1f}%)\n")
            
            f.write("\n## Sentiment Analysis\n\n")
            f.write("| Phone Number | Total Messages | Positive | Neutral | Negative | Positive % |\n")
            f.write("|-------------|---------------|----------|---------|----------|------------|\n")
            
            for number, stats in sentiment_by_number.items():
                positive_pct = (stats['positive'] / stats['total'] * 100) if stats['total'] > 0 else 0
                f.write(f"| {number} | {stats['total']} | {stats['positive']} | {stats['neutral']} | {stats['negative']} | {positive_pct:.1f}% |\n")
            
            f.write("\n## Keyword Analysis\n\n")
            f.write("| Phone Number | Positive Relationship | Parental Care | Child Welfare |\n")
            f.write("|-------------|----------------------|--------------|---------------|\n")
            
            for number, stats in keyword_by_number.items():
                f.write(f"| {number} | {stats['positive_relationship']} | {stats['parental_care']} | {stats['child_welfare']} |\n")
            
            f.write("\n## Key Evidence Categories\n\n")
            
            # Positive relationships
            f.write(f"### Positive Relationships and Intentions\n\n")
            f.write(f"*{len(positive_relationship_evidence)} messages identified*\n\n")
            f.write("#### Top Evidence Examples:\n\n")
            
            # Write top 5 examples
            for i, evidence in enumerate(positive_relationship_evidence[:5], 1):
                f.write(f"**Example {i}:**\n")
                f.write(f"- **From:** {evidence['from_number']}\n")
                f.write(f"- **Date:** {evidence['timestamp']}\n")
                f.write(f"- **Message:** {evidence['message_text']}\n")
                f.write(f"- **Sentiment:** {evidence['sentiment_category']} (score: {evidence['sentiment_compound']:.2f})\n")
                f.write(f"- **Keywords:** {evidence['positive_relationship_keywords']}\n\n")
            
            # Parental care
            f.write(f"### Parental Care and Love\n\n")
            f.write(f"*{len(parental_care_evidence)} messages identified*\n\n")
            f.write("#### Top Evidence Examples:\n\n")
            
            # Write top 5 examples
            for i, evidence in enumerate(parental_care_evidence[:5], 1):
                f.write(f"**Example {i}:**\n")
                f.write(f"- **From:** {evidence['from_number']}\n")
                f.write(f"- **Date:** {evidence['timestamp']}\n")
                f.write(f"- **Message:** {evidence['message_text']}\n")
                f.write(f"- **Sentiment:** {evidence['sentiment_category']} (score: {evidence['sentiment_compound']:.2f})\n")
                f.write(f"- **Keywords:** {evidence['parental_care_keywords']}\n\n")
            
            # Child welfare
            f.write(f"### Child Welfare Prioritization\n\n")
            f.write(f"*{len(child_welfare_evidence)} messages identified*\n\n")
            f.write("#### Top Evidence Examples:\n\n")
            
            # Write top 5 examples
            for i, evidence in enumerate(child_welfare_evidence[:5], 1):
                f.write(f"**Example {i}:**\n")
                f.write(f"- **From:** {evidence['from_number']}\n")
                f.write(f"- **Date:** {evidence['timestamp']}\n")
                f.write(f"- **Message:** {evidence['message_text']}\n")
                f.write(f"- **Sentiment:** {evidence['sentiment_category']} (score: {evidence['sentiment_compound']:.2f})\n")
                f.write(f"- **Keywords:** {evidence['child_welfare_keywords']}\n\n")
            
            f.write("## Recommendations for Legal Team\n\n")
            f.write("1. **Review highlighted messages:** Focus on the messages identified in each evidence category.\n")
            f.write("2. **Consider message context:** The local sentiment analysis provides a starting point, but context is important.\n")
            f.write("3. **Validate with expert review:** When API access is available, use GPT-4 for more nuanced analysis.\n")
            f.write("4. **Look for patterns:** Consider the timing and sequence of positive messages.\n\n")
            
            f.write("## Next Steps\n\n")
            f.write("1. Review the full CSV output for additional insights.\n")
            f.write("2. When API quota is available, run the full sentiment analysis with GPT-4.\n")
            f.write("3. Compare the local analysis with the GPT-4 analysis for validation.\n\n")
            
            f.write("---\n\n")
            f.write("*This report is confidential and intended solely for use by Tia's legal defense team.*\n")
        
        logger.info(f"Generated summary report: {SUMMARY_FILE}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        return False

# Main function
def main():
    """Main function to run the local sentiment analysis"""
    logger.info("Starting local sentiment analysis")
    
    # Print script information
    print("Local Sentiment Analysis for Legal Evidence")
    print("==========================================")
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
        # Setup NLTK
        setup_nltk()
        
        # Load input data
        print("Loading messages from CSV...")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            messages = list(reader)
        
        logger.info(f"Loaded {len(messages)} messages from {INPUT_FILE}")
        print(f"Loaded {len(messages)} messages from {INPUT_FILE}")
        
        # Process messages
        print("Analyzing messages...")
        results, sentiment_by_number, keyword_by_number = process_messages(messages)
        
        # Save results
        if results:
            print("Saving results to CSV...")
            success = save_results_to_csv(results)
            if success:
                print(f"Successfully saved {len(results)} analyzed messages to {OUTPUT_FILE}")
            
            # Generate summary report
            print("Generating summary report...")
            summary_success = generate_summary_report(results, sentiment_by_number, keyword_by_number)
            if summary_success:
                print(f"Generated summary report: {SUMMARY_FILE}")
        else:
            logger.warning("No results to save")
            print("Warning: No results were generated from the analysis")
        
        logger.info("Local sentiment analysis completed")
        print("\nAnalysis completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Error in local sentiment analysis: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

