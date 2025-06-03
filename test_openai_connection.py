#!/usr/bin/env python3
# test_openai_connection.py
# Script to verify OpenAI API key loading and connection

import os
import sys
import time
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

def test_openai_connection():
    """Test OpenAI API key loading and connection"""
    
    print("OpenAI API Connection Test")
    print("=========================")
    
    # Step 1: Check if .env file exists
    dotenv_path = Path(__file__).parent / '.env'
    print(f"\nChecking for .env file at: {dotenv_path}")
    
    if not dotenv_path.exists():
        print("ERROR: .env file not found!")
        return False
    
    print("SUCCESS: .env file found")
    
    # Step 2: Load environment variables
    print("\nLoading environment variables from .env file...")
    load_dotenv(dotenv_path)
    
    # Step 3: Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return False
    
    # Mask API key for display
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
    print(f"SUCCESS: OPENAI_API_KEY found in environment variables: {masked_key}")
    
    # Step 4: Configure OpenAI client (new API format)
    print("\nConfiguring OpenAI client...")
    try:
        client = OpenAI(api_key=api_key)
        print("SUCCESS: OpenAI client configured")
    except Exception as e:
        print(f"ERROR: Failed to configure OpenAI client: {e}")
        return False
    
    # Step 5: Test API connection
    print("\nTesting connection to OpenAI API...")
    try:
        start_time = time.time()
        
        # Make a simple request to test connectivity (new API format)
        response = client.chat.completions.create(
            model="gpt-4",  # Use same model as in main script
            messages=[
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Say 'Connection successful' if you can read this."}
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Extract response (new API format)
        response_text = response.choices[0].message.content.strip()
        
        print(f"SUCCESS: Received response from OpenAI API in {response_time:.2f} seconds")
        print(f"Response: '{response_text}'")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to connect to OpenAI API: {e}")
        print(f"Error details: {str(e)}")
        return False

def main():
    """Main function"""
    success = test_openai_connection()
    
    print("\nTest Results")
    print("===========")
    if success:
        print("✅ OpenAI API connection test PASSED")
        print("You can proceed with running the sentiment analysis script.")
        return 0
    else:
        print("❌ OpenAI API connection test FAILED")
        print("Please fix the issues above before proceeding with sentiment analysis.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

