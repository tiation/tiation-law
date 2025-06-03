# Message Sentiment Analysis

## Overview
This project provides sentiment analysis for text messages, specifically designed to analyze message content and extract emotional patterns, sentiments, and unspoken positive beliefs. The system is particularly focused on analyzing messages between specific phone numbers to identify positive sentiments and relationships.

### Key Features
- Analyzes message sentiment using OpenAI's GPT-4/GPT-3.5 models
- Extracts unspoken positive beliefs from message content
- Processes large message datasets with checkpointing
- Provides detailed sentiment analysis reports
- Handles message batching and rate limiting
- Includes progress tracking and error handling

## Requirements

### Dependencies
- Python 3.8 or higher
- OpenAI API key
- Required Python packages:
  ```
  pandas
  openai
  python-dotenv
  tqdm
  backoff
  ```

### Input Data Format
The input CSV file should contain the following columns:
- timestamp
- from_number
- direction
- message_text
- message_type

## Installation

1. Clone or download the project to your local machine:
   ```
   C:\Users\admin\Documents\sentiment_analysis\
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

## Configuration

### config.py Settings
Key configuration options in `src/config.py`:

```python
API_CONFIG = {
    "model": "gpt-4",  # Or "gpt-3.5-turbo"
    "max_tokens": 150,
    "temperature": 0.3
}

BATCH_CONFIG = {
    "batch_size": 50,
    "max_retries": 3,
    "retry_delay": 5
}
```

### Phone Numbers
Configure target phone numbers in `config.py`:
```python
PHONE_NUMBERS = {
    "TARGET_1": "6128856087",  # Number to analyze for good feelings
    "TARGET_2": "61428856087"  # Number to analyze for children-related sentiment
}
```

## Usage

### Basic Usage
```powershell
# Run with default settings
python -m sentiment_analysis.main

# Specify input file
python -m sentiment_analysis.main --input "path/to/messages.csv"

# Specify output file
python -m sentiment_analysis.main --output "path/to/output.csv"
```

### Additional Options
```powershell
# Resume from last checkpoint
python -m sentiment_analysis.main --resume

# Skip backup creation
python -m sentiment_analysis.main --no-backup

# Clear existing checkpoint
python -m sentiment_analysis.main --clear-checkpoint
```

## Output Format

### Results CSV
The analysis generates a CSV file with the following columns:
- timestamp: Original message timestamp
- from_number: Sender's phone number
- direction: Message direction
- message_text: Original message content
- message_type: Type of message
- sentiment: Analyzed sentiment
- unspoken_positive_beliefs: Extracted positive beliefs

### Analysis Summary
The program provides a summary including:
- Total messages analyzed
- Messages per phone number
- Analysis completion statistics
- Timestamp range of messages

## Progress Tracking
During analysis, the system displays:
- Current progress percentage
- Number of processed messages
- Average processing time
- Estimated completion time

## Error Handling
The system includes:
- Automatic retries for API failures
- Checkpointing for interrupted operations
- Detailed error logging
- Backup creation for output files

## Logging
Logs are stored in `sentiment_analysis.log` and include:
- Processing progress
- Error messages
- API interaction details
- System operations

## Important Notes
1. API Usage:
   - Monitors rate limits
   - Implements exponential backoff
   - Tracks token usage

2. Data Processing:
   - Handles large datasets
   - Preserves message order
   - Validates input data

3. Results:
   - Creates backups automatically
   - Provides detailed analysis
   - Supports resuming interrupted processing

## Troubleshooting
Common issues and solutions:

1. API Key Issues:
   - Verify .env file configuration
   - Check API key validity
   - Confirm environment variable loading

2. Data Format Issues:
   - Ensure CSV format matches requirements
   - Check column names
   - Verify data encoding

3. Processing Issues:
   - Use --resume for interrupted operations
   - Check log files for errors
   - Verify available disk space

## Support
For additional assistance or issues:
- Check the log file for detailed error messages
- Verify configuration settings
- Ensure all dependencies are installed correctly

