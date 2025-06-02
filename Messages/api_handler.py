import time
import logging
from typing import List, Dict, Any, Callable, Optional
import functools
from datetime import datetime, timedelta
import backoff
import openai
from openai import OpenAI
from collections import deque
import json

from .config import (
    API_CONFIG,
    BATCH_CONFIG,
    LOG_FILE
)

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter implementation using token bucket algorithm
    """
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_timestamps = deque(maxlen=requests_per_minute)
        self.token_usage = deque(maxlen=100)  # Track recent token usage
        
    def wait_if_needed(self, tokens_needed: int) -> None:
        """
        Wait if necessary to comply with rate limits
        """
        current_time = datetime.now()
        
        # Clean up old timestamps
        while self.request_timestamps and \
              (current_time - self.request_timestamps[0]).total_seconds() > 60:
            self.request_timestamps.popleft()
            
        # Clean up old token usage
        while self.token_usage and \
              (current_time - self.token_usage[0][1]).total_seconds() > 60:
            self.token_usage.popleft()
            
        # Check request rate limit
        if len(self.request_timestamps) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.request_timestamps[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                
        # Check token rate limit
        current_token_usage = sum(tokens for tokens, _ in self.token_usage)
        if current_token_usage + tokens_needed > self.tokens_per_minute:
            sleep_time = 60 - (current_time - self.token_usage[0][1]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Token limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                
        # Update tracking
        self.request_timestamps.append(current_time)
        self.token_usage.append((tokens_needed, current_time))

class OpenAIHandler:
    """
    Handles interactions with OpenAI API including rate limiting and retries
    """
    def __init__(self):
        self.api_key = API_CONFIG["api_key"]
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        self.client = OpenAI(api_key=self.api_key)
        self.model = API_CONFIG["model"]
        self.max_tokens = API_CONFIG["max_tokens"]
        self.temperature = API_CONFIG["temperature"]
        
        self.rate_limiter = RateLimiter(
            BATCH_CONFIG["rate_limit"]["requests_per_minute"],
            BATCH_CONFIG["rate_limit"]["tokens_per_minute"]
        )
        
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string
        """
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4 + 1
        
    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APIError),
        max_tries=BATCH_CONFIG["max_retries"],
        max_time=300
    )
    def _make_api_call(self, messages: List[Dict[str, str]]) -> str:
        """
        Make an API call with retry mechanism
        """
        try:
            # Estimate tokens needed
            total_tokens = sum(self._estimate_tokens(msg["content"]) for msg in messages)
            self.rate_limiter.wait_if_needed(total_tokens)
            
            # Log API request attempt
            logger.info("Making API call to OpenAI")
            logger.debug(f"Using model: {self.model}")
            logger.debug(f"Estimated tokens: {total_tokens}")
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,  # Slight penalty for repetition
                frequency_penalty=0.1,  # Slight penalty for repetition
            )
            
            # Log successful API call
            logger.info("API call successful")
            logger.debug(f"Response: {response.choices[0].message.content[:100]}...")
            
            return response.choices[0].message.content.strip()
            
        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise
        except openai.APIError as e:
            logger.error(f"API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API call: {str(e)}")
            raise
            
    def process_message(self, system_prompt: str, user_message: str) -> str:
        """
        Process a single message with the API
        """
        logger.debug(f"Processing message with system prompt: {system_prompt[:100]}...")
        logger.debug(f"User message: {user_message[:100]}...")
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"""
                Please analyze the following message in the context provided above.
                Provide a clear, concise analysis that would be suitable for legal review.
                
                Message to analyze: {user_message}
                
                Note: Focus only on positive elements and constructive interpretations.
                """
            }
        ]
        
        try:
            # Log API request details
            logger.debug(f"Sending API request with messages: {json.dumps(messages, indent=2)}")
            
            response = self._make_api_call(messages)
            
            # Log API response
            logger.debug(f"Received API response: {response[:100]}...")
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            logger.error(f"Failed message content: {user_message[:100]}...")
            return ""
            
    def process_batch(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        process_func: Callable[[str, str], Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of messages
        """
        results = []
        batch_size = BATCH_CONFIG["batch_size"]
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} of {len(messages)//batch_size + 1}")
            
            for message in batch:
                try:
                    analysis_result = process_func(system_prompt, message["message_text"])
                    message.update(analysis_result)
                    results.append(message)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    # Add message with empty analysis results
                    message.update({"sentiment": "", "unspoken_positive_beliefs": ""})
                    results.append(message)
                    
        return results
        
    def check_api_access(self) -> bool:
        """
        Verify API access and credentials
        """
        try:
            logger.info("Verifying API access...")
            
            if not self.api_key:
                logger.error("No API key found")
                return False
                
            # Test API access with a simple query
            test_messages = [
                {
                    "role": "system",
                    "content": "You are a test system verifying API access."
                },
                {
                    "role": "user",
                    "content": "Please respond with 'API access verified' if you receive this message."
                }
            ]
            
            response = self._make_api_call(test_messages)
            
            # Log verification result
            logger.info("API access verification successful")
            logger.debug(f"Test response: {response}")
            
            return "API access verified" in response
            
        except Exception as e:
            logger.error(f"API access check failed: {str(e)}")
            return False

