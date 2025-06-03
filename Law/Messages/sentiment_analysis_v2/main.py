#!/usr/bin/env python3
import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

from .config import (
    INPUT_FILE,
    OUTPUT_DIR,
    LOG_FILE,
    PHONE_NUMBERS,
    API_CONFIG
)
from .data_loader import MessageDataLoader
from .sentiment_analyzer import SentimentAnalyzer
from .output_processor import OutputProcessor
from .api_handler import OpenAIHandler

# Set up logging
def setup_logging():
    """
    Configure logging with both file and console handlers
    """
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    return root_logger

logger = setup_logging()

def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up command line argument parser
    """
    parser = argparse.ArgumentParser(
        description="Sentiment Analysis for Message Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m sentiment_analysis.main
    python -m sentiment_analysis.main --input path/to/messages.csv
    python -m sentiment_analysis.main --resume
    python -m sentiment_analysis.main --no-backup
    """
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Path to input CSV file (default: %(default)s)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "sentiment_analysis_results.csv",
        help="Path to output CSV file (default: %(default)s)"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint if available"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup of existing output file"
    )
    
    parser.add_argument(
        "--clear-checkpoint",
        action="store_true",
        help="Clear existing checkpoint before starting"
    )
    
    return parser

def check_environment() -> Optional[str]:
    """
    Check if all required environment variables and dependencies are set up
    """
    if not API_CONFIG["api_key"]:
        return "OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
        
    try:
        api_handler = OpenAIHandler()
        if not api_handler.check_api_access():
            return "Failed to verify OpenAI API access. Please check your API key and internet connection."
    except Exception as e:
        return f"Error checking API access: {str(e)}"
        
    return None

def display_progress(stats: Dict[str, Any]) -> None:
    """
    Display progress information to the console
    """
    print("\nAnalysis Progress:")
    print(f"Total Messages: {stats['total_messages']}")
    print(f"Processed Messages: {stats['processed_messages']}")
    print(f"Completion: {stats['completion_percentage']:.2f}%")
    print(f"Elapsed Time: {stats['elapsed_time']:.2f} seconds")
    print(f"Average Time per Message: {stats['average_time_per_message']:.2f} seconds")
    print()

def main() -> int:
    """
    Main execution function
    """
    logger.debug("Starting sentiment analysis application")
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Check environment
    logger.debug("Checking environment configuration...")
    if error := check_environment():
        logger.error(error)
        print(f"Error: {error}", file=sys.stderr)
        return 1
    logger.debug("Environment check passed")
        
    try:
        # Initialize components
        logger.debug("Initializing system components...")
        data_loader = MessageDataLoader(args.input)
        logger.debug("Data loader initialized")
        
        sentiment_analyzer = SentimentAnalyzer()
        logger.debug("Sentiment analyzer initialized")
        
        output_processor = OutputProcessor(args.output)
        logger.debug("Output processor initialized")
        
        # Clear checkpoint if requested
        if args.clear_checkpoint:
            sentiment_analyzer.clear_checkpoint()
            
        # Load and preprocess data
        logger.debug("Starting data loading and preprocessing...")
        print("Loading message data...")
        messages = data_loader.get_messages_for_analysis()
        logger.debug(f"Loaded {len(messages)} messages for analysis")
        
        if not messages:
            logger.error("No messages found for analysis")
            print("Error: No messages found for analysis", file=sys.stderr)
            return 1
            
        # Display initial statistics
        message_counts = data_loader.get_message_count()
        print("\nMessage Counts:")
        for number_type, count in message_counts.items():
            print(f"{number_type}: {count} messages")
            
        # Perform sentiment analysis
        logger.debug("Starting sentiment analysis process...")
        print("\nPerforming sentiment analysis...")
        processed_messages = sentiment_analyzer.analyze_messages(
            messages,
            resume=args.resume
        )
        logger.debug("Sentiment analysis completed")
        
        # Display progress periodically
        while sentiment_analyzer.get_analysis_statistics()["completion_percentage"] < 100:
            stats = sentiment_analyzer.get_analysis_statistics()
            display_progress(stats)
            time.sleep(5)  # Update every 5 seconds
            
        # Save results
        print("\nSaving analysis results...")
        success = output_processor.save_results(
            processed_messages,
            create_backup=not args.no_backup
        )
        
        if not success:
            logger.error("Failed to save analysis results")
            print("Error: Failed to save analysis results", file=sys.stderr)
            return 1
            
        # Generate and display summary
        print("\nGenerating analysis summary...")
        summary = output_processor.generate_summary(processed_messages)
        
        print("\nAnalysis Summary:")
        print(f"Total Messages Analyzed: {summary['total_messages']}")
        print("\nMessages by Phone Number:")
        for number, count in summary['messages_by_number'].items():
            print(f"  {number}: {count} messages")
            
        print("\nAnalysis Completion:")
        print(f"Messages with Sentiment: {summary['analysis_completion']['with_sentiment']}")
        print(f"Messages with Beliefs: {summary['analysis_completion']['with_beliefs']}")
        
        print("\nTimestamp Range:")
        print(f"Start: {summary['timestamp_range']['start']}")
        print(f"End: {summary['timestamp_range']['end']}")
        
        print(f"\nResults saved to: {args.output}")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        print("\nAnalysis interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

