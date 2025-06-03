import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# File paths
INPUT_FILE = INPUT_DIR / "both_numbers_messages.csv"
OUTPUT_FILE = OUTPUT_DIR / "sentiment_analysis_results.csv"
LOG_FILE = PROJECT_ROOT / "sentiment_analysis.log"

# Phone numbers to analyze
PHONE_NUMBERS = {
    "TARGET_1": "6128856087",  # Number to analyze for good feelings towards others
    "TARGET_2": "61428856087"  # Number to analyze for love towards children
}

# OpenAI API Configuration
API_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "model": "gpt-4",  # Using GPT-4 for more nuanced analysis
    "max_tokens": 250,  # Increased for more detailed analysis
    "temperature": 0.2,  # Very low temperature for more consistent, focused analysis
}

# Batch Processing Settings
BATCH_CONFIG = {
    "batch_size": 25,  # Smaller batch size for more careful analysis
    "max_retries": 5,  # Increased retries for reliability
    "retry_delay": 10,  # Longer delay between retries
    "rate_limit": {
        "requests_per_minute": 40,  # Conservative rate limiting
        "tokens_per_minute": 80000,  # Adjusted for detailed responses
    }
}

# Analysis Settings
ANALYSIS_CONFIG = {
    "sentiment_prompt_template": """
    You are a legal sentiment analyst examining messages for evidence of positive relationships and good intentions. Analyze this message with particular attention to emotional tone and underlying attitudes:

    MESSAGE: "{message}"
    SENDER NUMBER: {target_number}

    ANALYSIS FOCUS:
    If sender is {target_1}:
    - Look for ANY evidence of good feelings, positive intentions, or goodwill towards others
    - Identify language that shows respect, care, or consideration
    - Note any signs of attempting to maintain positive relationships
    - Highlight evidence of peaceful or constructive intentions

    If sender is {target_2}:
    - Look for ANY expressions of parental love and care
    - Identify language showing concern for children's wellbeing
    - Note emotional investment in children's lives
    - Highlight nurturing or protective parental behaviors

    Provide a clear, objective analysis suitable for legal review.
    """,
    
    "beliefs_prompt_template": """
    You are conducting a legal analysis of underlying positive beliefs and intentions in communications. Examine this message for unspoken positive attitudes and motivations:

    MESSAGE: "{message}"
    SENDER NUMBER: {target_number}

    ANALYSIS FOCUS:
    If sender is {target_1}:
    - Identify implicit signs of goodwill or positive regard
    - Uncover underlying peaceful or constructive motivations
    - Note subtle indicators of respect or consideration
    - Look for context suggesting positive relationship intentions

    If sender is {target_2}:
    - Identify implicit expressions of parental love
    - Uncover underlying concern for children's wellbeing
    - Note subtle indicators of parental dedication
    - Look for context suggesting nurturing parental attitudes

    Focus on extracting positive beliefs that may not be explicitly stated but are evidenced by the message content and context.
    Remember to be thorough and objective in your analysis for legal review purposes.
    """,

    "save_checkpoint_interval": 100,  # Save progress every 100 messages
    "logging_level": "INFO"
}

# CSV Configuration
CSV_CONFIG = {
    "encoding": "utf-8",
    "errors": "replace",
    "required_columns": [
        "timestamp",
        "from_number",
        "direction",
        "message_text",
        "message_type"
    ],
    "output_columns": [
        "timestamp",
        "from_number",
        "direction",
        "message_text",
        "message_type",
        "sentiment",
        "unspoken_positive_beliefs"
    ]
}

