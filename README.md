# iPhone Message Extraction and Sentiment Analysis

## 1. Overview of the Message Extraction and Analysis Process

This project provides a systematic approach to extract text messages from iPhone backups, process them into a standardized format, and analyze their sentiment content for legal defense purposes. The system specifically targets:

- Messages from specific phone numbers (6128856087 and 61428856087)
- Communications with the contact "TLSPayphone"
- Various Australian mobile numbers of interest

The extracted messages undergo sentiment analysis to identify:
- Evidence of positive relationships and good intentions
- Expressions of parental love and care
- Language showing concern for children's wellbeing
- Signs of attempting to maintain positive relationships

This documentation is designed to support legal defense teams in analyzing communications related to "tia" and extracting sentiment patterns that may be relevant to legal proceedings.

## 2. Requirements and Setup Instructions

### Prerequisites:
- Python 3.7+ environment
- iPhone backup (unencrypted or decrypted) accessible on your system
- iPhone backup extraction tool (one of the following):
  - iPhone Backup Extractor
  - iExplorer
  - SQLite browser (for direct database access)

### Environment Setup:
1. Clone this repository to your local machine
2. Install required Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure you have your OpenAI API key if using the sentiment analysis component:
   - Create a `.env` file in the project root
   - Add your API key: `OPENAI_API_KEY=your_key_here`

## 3. Step-by-Step Process for Message Extraction

### Backup Creation and Access:
1. Create an unencrypted iPhone backup using iTunes/Finder
   - Connect iPhone to computer
   - Select "Back up all of the data on your iPhone to this computer"
   - Ensure "Encrypt iPhone backup" is NOT checked
   - Start backup process

2. Locate the backup directory:
   - Windows: `%APPDATA%\Apple Computer\MobileSync\Backup\`
   - macOS: `~/Library/Application Support/MobileSync/Backup/`

3. Extract message database:
   - Using iPhone Backup Extractor or similar tool
   - Locate and extract `sms.db` (SQLite database containing messages)

### Message Filtering and Extraction:
1. Open the `sms.db` file using a SQLite browser or query tool
2. Execute queries to extract messages from target numbers:
   ```sql
   SELECT 
       message.date AS timestamp,
       handle.id AS contact_identifier,
       CASE WHEN message.is_from_me = 0 THEN 'incoming' ELSE 'outgoing' END AS direction,
       message.text AS message_text,
       CASE 
           WHEN message.service = 'SMS' THEN 'SMS'
           WHEN message.service = 'iMessage' THEN 'iMessage'
           ELSE 'Other'
       END AS message_type
   FROM message
   JOIN handle ON message.handle_id = handle.ROWID
   WHERE handle.id IN ('6128856087', '61428856087', 'TLSPayphone')
      OR handle.id LIKE '+61%'
      OR handle.id LIKE '04%'
   ORDER BY message.date;
   ```

3. Export the query results to CSV format
4. Transform the timestamp from Apple's format (seconds since 2001-01-01) to standard datetime format

## 4. CSV Format Specifications

The extracted messages must be formatted in a CSV file with the following specifications:

- **Filename**: `both_numbers_messages.csv`
- **Location**: `[PROJECT_ROOT]/data/input/`
- **Encoding**: UTF-8
- **Required Columns**:
  - `timestamp`: Message timestamp in YYYY-MM-DD HH:MM:SS format
  - `from_number`: Phone number of the message sender
  - `direction`: Either 'incoming' or 'outgoing'
  - `message_text`: The actual message content
  - `message_type`: Type of message (SMS, iMessage, MMS, etc.)

Example CSV format:
```
timestamp,from_number,direction,message_text,message_type
2023-01-01 12:34:56,6128856087,incoming,"Hello, how are you doing?",SMS
2023-01-01 12:35:23,61428856087,outgoing,"I'm doing well, thank you for asking.",iMessage
```

## 5. Integration with Existing Sentiment Analysis Pipeline

The `both_numbers_messages.csv` file is automatically processed by the sentiment analysis pipeline:

1. **Data Loading**: The system uses `data_loader.py` to:
   - Load the CSV file
   - Validate required columns
   - Clean message text (removing URLs, normalizing whitespace)
   - Filter by target phone numbers
   - Remove empty messages
   - Sort by timestamp

2. **Sentiment Analysis**: Each message is analyzed using:
   - GPT-4 for nuanced sentiment detection
   - Focus on positive relationships and good intentions
   - Analysis of parental love and care expressions
   - Identification of unspoken positive beliefs

3. **Output Generation**: Analysis results are saved to:
   - `data/output/sentiment_analysis_results.csv`
   - Includes original message plus sentiment analysis columns

To run the pipeline:
```
python -m sentiment_analysis.main
```

## 6. Validation Steps

After generating the CSV file and before running the sentiment analysis, perform these validation steps:

1. **Format Validation**:
   - Ensure CSV has all required columns
   - Check that timestamps are properly formatted
   - Verify phone numbers match expected format

2. **Content Validation**:
   - Confirm all target numbers are included
   - Sample message texts to ensure they're correctly extracted
   - Check that message direction is properly identified

3. **Integration Testing**:
   - Run a small subset through the pipeline to verify processing
   - Check log file for any warnings or errors
   - Validate that sentiment analysis is capturing relevant aspects

4. **Results Verification**:
   - Review sample of output for accuracy
   - Ensure messages related to "tia" are properly analyzed
   - Verify that positive relationship indicators are detected

## 7. Notes on Handling Sensitive Content

When working with message data for legal defense purposes:

1. **Data Privacy**:
   - Store extracted messages securely
   - Limit access to authorized personnel only
   - Consider password-protecting files containing sensitive information

2. **Context Preservation**:
   - Maintain complete message threads for proper context
   - Avoid selective extraction that might misrepresent conversations
   - Include metadata that helps establish message authenticity

3. **Content Types**:
   - Preserve various content types (D&D discussions, technical messages, personal communications)
   - Retain message formatting where possible for accurate sentiment analysis
   - Note any potential encrypted or deliberately obfuscated content

4. **Legal Considerations**:
   - Document the chain of custody for the message data
   - Record all processing steps to maintain evidential integrity
   - Note any limitations or assumptions made during extraction and analysis

5. **Sentiment Analysis Limitations**:
   - Be aware that automated sentiment analysis is interpretive
   - Highlight cases where context may be ambiguous
   - Consider human review for critical messages

By following this documentation, you should be able to successfully extract, process, and analyze iPhone messages for legal defense purposes, focusing on identifying positive relationship indicators and parental care expressions.

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

