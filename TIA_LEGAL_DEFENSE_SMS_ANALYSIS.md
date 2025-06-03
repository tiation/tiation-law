# iPhone Message Extraction and Sentiment Analysis for Legal Defense

## Project Overview

This document outlines the comprehensive process for extracting, organizing, and analyzing iPhone messages to support Tia's legal defense. The project leverages sentiment analysis to identify positive relationships, good intentions, parental care, and other evidence beneficial to the defense case.

## Target Phone Numbers

Messages will be extracted from the following numbers:
- +61 427 444 440
- TLSPayphone
- +61 488 180 171
- +61 404 720 244
- +61 439 447 043
- +61 436 595 509
- +61 432 654 627
- +61 437 816 851

## Directory Structure

```
C:\Users\admin\Documents\
├── sentiment_analysis\           # Main project directory
│   ├── data\                     # Data directory
│   │   ├── input\                # Input files for analysis
│   │   └── output\               # Output and results
│   ├── sentiment_analysis\       # Analysis code
│   ├── config\                   # Configuration files
│   └── TIA_LEGAL_DEFENSE_SMS_ANALYSIS.md # This documentation
└── iPhoneBackupExtracts\         # iPhone backup data
    ├── MessagesByContact\        # Messages organized by contact
    ├── sms_export.csv            # Raw SMS export
    └── messages_by_contact.csv   # Messages sorted by contact
```

## Process Workflow

### 1. Message Extraction

#### Source Data
The iPhone backup data is located in `C:\Users\admin\Documents\iPhoneBackupExtracts`. This directory contains various exports from the iPhone, including:
- `sms_export.csv`: Raw SMS messages
- `messages_by_contact.csv`: Messages organized by contact
- `both_numbers_messages.csv`: Messages from specific numbers

#### Extraction Methodology
1. Filter messages from the existing backup files for the target phone numbers
2. Format the extracted messages into a standardized CSV with the following columns:
   - timestamp: Date and time of the message
   - from_number: Sender's phone number
   - direction: "incoming" or "outgoing"
   - message_text: Content of the message
   - message_type: "SMS", "iMessage", etc.
3. Save the filtered messages to `sentiment_analysis\data\input\tia_case_messages.csv`

### 2. Sentiment Analysis

#### Analysis Configuration
The sentiment analysis system is configured in `sentiment_analysis\sentiment_analysis\config.py` with the following key settings:
- GPT-4 model with temperature 0.2 for consistent, focused analysis
- Batch processing with size of 25 messages per batch
- Conservative rate limiting to ensure API reliability
- Custom prompt templates focused on identifying positive relationships and parental care

#### Analysis Process
1. Load the filtered messages from the input CSV
2. Process each message through the sentiment analyzer with focus on:
   - Evidence of positive relationships and good intentions
   - Expressions of parental love and care
   - Signs of respect, consideration, and peaceful intentions
   - Indicators of child welfare concern and emotional investment
3. Generate sentiment scores and interpretations for each message
4. Save the annotated messages to `sentiment_analysis\data\output\sentiment_analysis_results.csv`

### 3. Legal Evidence Collection

#### Evidence Focus
The analysis will highlight messages that demonstrate:
- Positive intentions and goodwill towards others
- Parental love and dedication
- Constructive relationship maintenance
- Child welfare prioritization

#### Evidence Organization
1. Sort and categorize messages by evidence type
2. Generate summary reports for each evidence category
3. Identify and highlight particularly strong evidence for legal review
4. Create a consolidated evidence package for the legal team

## Running the Analysis

### Prerequisites
- Python 3.8+
- OpenAI API key (set in .env file)
- Required Python packages: pandas, openai, dotenv, tqdm

### Step-by-Step Instructions

1. **Extract Messages**
   ```powershell
   python extract_messages.py --target-numbers "numbers.txt" --output "data/input/tia_case_messages.csv"
   ```

2. **Run Sentiment Analysis**
   ```powershell
   python run_sentiment_analysis.py --input "data/input/tia_case_messages.csv" --output "data/output/sentiment_analysis_results.csv"
   ```

3. **Generate Evidence Report**
   ```powershell
   python generate_legal_evidence.py --analysis "data/output/sentiment_analysis_results.csv" --output "data/output/legal_evidence_report.md"
   ```

## Interpreting Results

### Sentiment Analysis Output
The sentiment analysis results CSV contains the following columns:
- Original message columns (timestamp, from_number, etc.)
- `sentiment`: Overall sentiment score and interpretation
- `unspoken_positive_beliefs`: Analysis of implicit positive attitudes

### Evidence Strength Indicators
- **Strong Evidence**: Messages with explicit statements of care, love, or positive intent
- **Moderate Evidence**: Messages with implicit positive tone or constructive engagement
- **Supporting Evidence**: Messages that provide context for other evidence

### Guidance for Legal Team
1. Focus on "Strong Evidence" messages first
2. Look for patterns of consistent positive behavior over time
3. Note timestamp sequences that show sustained positive engagement
4. Pay attention to messages demonstrating parental prioritization

## Troubleshooting

### Common Issues
- **Missing messages**: Check filtering parameters in extract_messages.py
- **Analysis errors**: Verify API key in .env file
- **Incomplete results**: Check log file for rate limiting or API errors

### Support Resources
For technical assistance with the analysis process, contact the technical team at support@example.com.

---

*This documentation is confidential and intended solely for use by Tia's legal defense team.*

