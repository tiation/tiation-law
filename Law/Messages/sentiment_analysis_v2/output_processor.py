import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv
from datetime import datetime
from tqdm import tqdm

from .config import (
    CSV_CONFIG,
    OUTPUT_DIR,
    LOG_FILE,
    PHONE_NUMBERS
)

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OutputProcessor:
    """
    Handles the processing and saving of sentiment analysis results
    """
    def __init__(self, output_file: Optional[Path] = None):
        self.output_file = output_file or OUTPUT_DIR / "sentiment_analysis_results.csv"
        self.required_columns = CSV_CONFIG["required_columns"]
        self.output_columns = CSV_CONFIG["output_columns"]
        
    def _validate_results(self, results: List[Dict[str, Any]]) -> bool:
        """
        Validate that all required data is present in the results
        """
        if not results:
            logger.error("Empty results list provided")
            return False
            
        # Check for required columns
        required_fields = set(self.output_columns)
        for result in results:
            missing_fields = required_fields - set(result.keys())
            if missing_fields:
                logger.error(f"Missing required fields in result: {missing_fields}")
                return False
                
        return True
        
    def _format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a single result dictionary for output
        """
        formatted_result = {}
        
        try:
            # Ensure all required columns are present
            for column in self.output_columns:
                formatted_result[column] = result.get(column, "")
                
            # Format timestamp if needed
            if isinstance(formatted_result["timestamp"], (int, float)):
                formatted_result["timestamp"] = datetime.fromtimestamp(
                    formatted_result["timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")
                
            # Ensure phone number format is consistent
            if formatted_result["from_number"] in PHONE_NUMBERS.values():
                # Add any specific phone number formatting if needed
                pass
                
            # Clean and format text fields
            for field in ["message_text", "sentiment", "unspoken_positive_beliefs"]:
                if formatted_result.get(field):
                    formatted_result[field] = str(formatted_result[field]).strip()
                    
        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            # Return original result if formatting fails
            return result
            
        return formatted_result
        
    def _create_backup(self) -> None:
        """
        Create a backup of existing output file if it exists
        """
        if self.output_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.output_file.with_name(
                f"{self.output_file.stem}_backup_{timestamp}{self.output_file.suffix}"
            )
            try:
                self.output_file.rename(backup_file)
                logger.info(f"Created backup file: {backup_file}")
            except Exception as e:
                logger.error(f"Failed to create backup: {str(e)}")
                
    def save_results(self, results: List[Dict[str, Any]], create_backup: bool = True) -> bool:
        """
        Save analysis results to CSV file
        """
        if not self._validate_results(results):
            return False
            
        try:
            # Create output directory if it doesn't exist
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if requested
            if create_backup:
                self._create_backup()
                
            # Format results
            formatted_results = []
            for result in tqdm(results, desc="Formatting results"):
                formatted_result = self._format_result(result)
                formatted_results.append(formatted_result)
                
            # Write to CSV
            logger.info(f"Writing {len(formatted_results)} results to {self.output_file}")
            
            with open(self.output_file, 'w', newline='', encoding=CSV_CONFIG["encoding"]) as f:
                writer = csv.DictWriter(f, fieldnames=self.output_columns)
                writer.writeheader()
                
                for result in tqdm(formatted_results, desc="Writing to CSV"):
                    writer.writerow(result)
                    
            logger.info("Results saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return False
            
    def load_results(self) -> Optional[pd.DataFrame]:
        """
        Load saved results from CSV file
        """
        try:
            if not self.output_file.exists():
                logger.error(f"Results file not found: {self.output_file}")
                return None
                
            df = pd.read_csv(
                self.output_file,
                encoding=CSV_CONFIG["encoding"],
                on_bad_lines='skip'  # Handle bad lines by skipping them
            )
            
            logger.info(f"Loaded {len(df)} results from {self.output_file}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading results: {str(e)}")
            return None
            
    def generate_summary(self, results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate summary statistics from the analysis results
        """
        try:
            # Load results from file if not provided
            if results is None:
                df = self.load_results()
                if df is None:
                    return {"error": "No results available"}
            else:
                df = pd.DataFrame(results)
                
            summary = {
                "total_messages": len(df),
                "messages_by_number": df["from_number"].value_counts().to_dict(),
                "analysis_completion": {
                    "total": len(df),
                    "with_sentiment": df["sentiment"].notna().sum(),
                    "with_beliefs": df["unspoken_positive_beliefs"].notna().sum()
                },
                "timestamp_range": {
                    "start": df["timestamp"].min(),
                    "end": df["timestamp"].max()
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {"error": str(e)}

