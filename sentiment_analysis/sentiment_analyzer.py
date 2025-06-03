import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import time
from datetime import datetime
from tqdm import tqdm
import openai
from openai import OpenAI

from .config import (
    ANALYSIS_CONFIG,
    PHONE_NUMBERS,
    OUTPUT_DIR,
    LOG_FILE,
    API_CONFIG
)
from .api_handler import OpenAIHandler

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Handles sentiment analysis and belief extraction from messages
    """
    def __init__(self):
        self.api_handler = OpenAIHandler()
        self.checkpoint_file = OUTPUT_DIR / "analysis_checkpoint.json"
        self.progress: Dict[str, Any] = self._load_checkpoint()
        
        # Verify API access
        if not self.api_handler.check_api_access():
            raise ValueError("Failed to verify OpenAI API access")
        
    def _load_checkpoint(self) -> Dict[str, Any]:
        """
        Load progress from checkpoint file if it exists
        """
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading checkpoint: {str(e)}")
                
        return {
            "last_processed_index": 0,
            "processed_messages": [],
            "start_time": datetime.now().isoformat(),
            "total_messages": 0
        }
        
    def _save_checkpoint(self, processed_messages: List[Dict[str, Any]], current_index: int) -> None:
        """
        Save current progress to checkpoint file
        """
        try:
            self.progress["last_processed_index"] = current_index
            self.progress["processed_messages"] = processed_messages
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.progress, f)
                
        except Exception as e:
            logger.error(f"Error saving checkpoint: {str(e)}")
            
    def _get_phone_number_type(self, phone_number: str) -> str:
        """
        Get the type (TARGET_1 or TARGET_2) for a given phone number
        """
        for number_type, number in PHONE_NUMBERS.items():
            if number == phone_number:
                return number_type
        return "UNKNOWN"

    def _format_sentiment_prompt(self, message: str, phone_number: str) -> str:
        """
        Format the sentiment analysis prompt for a specific message
        """
        target_1 = PHONE_NUMBERS["TARGET_1"]
        target_2 = PHONE_NUMBERS["TARGET_2"]
        
        template = ANALYSIS_CONFIG["sentiment_prompt_template"]
        return template.format(
            message=message,
            target_number=phone_number,
            target_1=target_1,
            target_2=target_2
        )
        
    def _format_beliefs_prompt(self, message: str, phone_number: str) -> str:
        """
        Format the beliefs analysis prompt for a specific message
        """
        target_1 = PHONE_NUMBERS["TARGET_1"]
        target_2 = PHONE_NUMBERS["TARGET_2"]
        
        template = ANALYSIS_CONFIG["beliefs_prompt_template"]
        return template.format(
            message=message,
            target_number=phone_number,
            target_1=target_1,
            target_2=target_2
        )
        
    def _analyze_message(self, message: Dict[str, Any]) -> Dict[str, str]:
        """
        Analyze a single message for both sentiment and beliefs
        """
        phone_number = message["from_number"]
        message_text = message["message_text"]
        
        # Validate phone number
        if phone_number not in PHONE_NUMBERS.values():
            logger.error(f"Unknown phone number: {phone_number}")
            return {
                "sentiment": "ERROR: Unknown phone number",
                "unspoken_positive_beliefs": "ERROR: Unknown phone number"
            }
            
        logger.info(f"Starting analysis for message from {phone_number}")
        logger.debug(f"Message content (truncated): {message_text[:100]}...")
        
        try:
            # Format prompts with proper variables
            sentiment_prompt = self._format_sentiment_prompt(message_text, phone_number)
            beliefs_prompt = self._format_beliefs_prompt(message_text, phone_number)
            
            # Get sentiment analysis
            logger.info("Performing sentiment analysis...")
            sentiment = self.api_handler.process_message(sentiment_prompt, "")
            logger.debug(f"Raw sentiment analysis response: {sentiment[:200]}")
            
            # Add delay between API calls
            time.sleep(0.5)
            
            # Get beliefs analysis
            logger.info("Performing beliefs analysis...")
            beliefs = self.api_handler.process_message(beliefs_prompt, "")
            logger.debug(f"Raw beliefs analysis response: {beliefs[:200]}")
            
            # Add delay between messages
            time.sleep(0.5)
            
            # Validate responses
            if not sentiment or not beliefs:
                raise ValueError("Empty response from API")
                
            logger.info("Analysis completed successfully")
            
            return {
                "sentiment": sentiment.strip(),
                "unspoken_positive_beliefs": beliefs.strip()
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error analyzing message: {error_msg}")
            logger.error(f"Failed message details: number={phone_number}, text_preview={message_text[:50]}")
            
            return {
                "sentiment": f"ERROR: Analysis failed - {error_msg}",
                "unspoken_positive_beliefs": f"ERROR: Analysis failed - {error_msg}"
            }
        
    def analyze_messages(self, messages: List[Dict[str, Any]], resume: bool = True) -> List[Dict[str, Any]]:
        """
        Analyze a list of messages with progress tracking and checkpointing
        """
        if resume and self.progress["processed_messages"]:
            start_index = self.progress["last_processed_index"]
            processed_messages = self.progress["processed_messages"]
            logger.info(f"Resuming from message {start_index + 1}")
        else:
            start_index = 0
            processed_messages = []
            self.progress["start_time"] = datetime.now().isoformat()
            self.progress["total_messages"] = len(messages)
            
        try:
            # Create progress bar
            pbar = tqdm(
                total=len(messages),
                initial=start_index,
                desc="Analyzing messages"
            )
            
            # Process messages
            for i in range(start_index, len(messages)):
                message = messages[i]
                
                # Skip if message was already processed
                if i < len(processed_messages):
                    pbar.update(1)
                    continue
                    
                # Analyze message
                try:
                    logger.info(f"Processing message {i + 1}/{len(messages)}")
                    analysis_results = self._analyze_message(message)
                    message.update(analysis_results)
                    processed_messages.append(message)
                    
                    # Save checkpoint periodically
                    if (i + 1) % ANALYSIS_CONFIG["save_checkpoint_interval"] == 0:
                        self._save_checkpoint(processed_messages, i)
                        logger.info(f"Checkpoint saved at message {i + 1}")
                        
                except Exception as e:
                    logger.error(f"Error processing message {i + 1}: {str(e)}")
                    message.update({
                        "sentiment": "ERROR: Analysis failed",
                        "unspoken_positive_beliefs": "ERROR: Analysis failed"
                    })
                    processed_messages.append(message)
                    
                pbar.update(1)
                
            pbar.close()
            
            # Save final checkpoint
            self._save_checkpoint(processed_messages, len(messages) - 1)
            logger.info("Analysis completed successfully")
            
            return processed_messages
            
        except Exception as e:
            logger.error(f"Error during message analysis: {str(e)}")
            raise
            
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the analysis process
        """
        if not self.progress["processed_messages"]:
            return {"status": "No analysis performed yet"}
            
        start_time = datetime.fromisoformat(self.progress["start_time"])
        elapsed_time = (datetime.now() - start_time).total_seconds()
        total_messages = self.progress["total_messages"]
        processed_count = len(self.progress["processed_messages"])
        
        return {
            "total_messages": total_messages,
            "processed_messages": processed_count,
            "completion_percentage": (processed_count / total_messages) * 100 if total_messages > 0 else 0,
            "elapsed_time": elapsed_time,
            "average_time_per_message": elapsed_time / processed_count if processed_count > 0 else 0
        }
        
    def clear_checkpoint(self) -> None:
        """
        Clear the existing checkpoint file
        """
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            self.progress = self._load_checkpoint()
            logger.info("Checkpoint cleared")

