import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
import re

from .config import (
    CSV_CONFIG,
    PHONE_NUMBERS,
    INPUT_FILE,
    LOG_FILE
)

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageDataLoader:
    """
    Handles loading and preprocessing of message data from CSV files.
    """
    
    def __init__(self, input_file: Path = INPUT_FILE):
        self.input_file = input_file
        self.data: Optional[pd.DataFrame] = None
        self.required_columns = CSV_CONFIG["required_columns"]
        
    def load_data(self) -> pd.DataFrame:
        """
        Load message data from CSV file with proper error handling.
        """
        try:
            logger.info(f"Loading data from {self.input_file}")
            self.data = pd.read_csv(
                self.input_file,
                encoding=CSV_CONFIG["encoding"],
                on_bad_lines='skip'  # Handle bad lines by skipping them
            )
            self._validate_columns()
            return self.data
        except FileNotFoundError as e:
            logger.error(f"Input file not found: {self.input_file}")
            raise FileNotFoundError(f"Could not find input file: {self.input_file}") from e
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
            
    def _validate_columns(self) -> None:
        """
        Validate that all required columns are present in the data.
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        missing_columns = set(self.required_columns) - set(self.data.columns)
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    def preprocess_data(self) -> pd.DataFrame:
        """
        Preprocess the loaded data by cleaning and filtering messages.
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        logger.info("Starting data preprocessing")
        
        try:
            # Create a copy to avoid modifying original data
            processed_data = self.data.copy()
            
            # Clean message text
            processed_data['message_text'] = processed_data['message_text'].apply(self._clean_message)
            
            # Filter for target phone numbers
            processed_data = self._filter_target_numbers(processed_data)
            
            # Remove empty messages
            processed_data = self._remove_empty_messages(processed_data)
            
            # Sort by timestamp
            processed_data = self._sort_by_timestamp(processed_data)
            
            logger.info(f"Preprocessing complete. Remaining messages: {len(processed_data)}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error during preprocessing: {str(e)}")
            raise
            
    def _clean_message(self, message: str) -> str:
        """
        Clean message text by removing unwanted characters and normalizing whitespace.
        """
        if not isinstance(message, str):
            return ""
            
        # Remove any URL links
        message = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', message)
        
        # Remove special characters but keep basic punctuation
        message = re.sub(r'[^\w\s.,!?-]', '', message)
        
        # Normalize whitespace
        message = ' '.join(message.split())
        
        return message.strip()
        
    def _filter_target_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter messages to include only those from target phone numbers.
        """
        target_numbers = list(PHONE_NUMBERS.values())
        return df[df['from_number'].isin(target_numbers)]
        
    def _remove_empty_messages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows with empty or whitespace-only messages.
        """
        return df[df['message_text'].str.strip().str.len() > 0]
        
    def _sort_by_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sort messages by timestamp in ascending order.
        """
        return df.sort_values('timestamp')
        
    def get_messages_for_analysis(self) -> List[Dict]:
        """
        Get messages prepared for sentiment analysis.
        """
        if self.data is None:
            self.load_data()
            
        processed_data = self.preprocess_data()
        
        messages = []
        for _, row in processed_data.iterrows():
            message_dict = {
                'timestamp': row['timestamp'],
                'from_number': row['from_number'],
                'message_text': row['message_text'],
                'direction': row['direction'],
                'message_type': row['message_type'],
            }
            messages.append(message_dict)
            
        return messages
        
    def get_message_count(self) -> Dict[str, int]:
        """
        Get count of messages for each target phone number.
        """
        if self.data is None:
            self.load_data()
            
        processed_data = self.preprocess_data()
        
        counts = {
            number_type: len(processed_data[processed_data['from_number'] == number])
            for number_type, number in PHONE_NUMBERS.items()
        }
        
        return counts

