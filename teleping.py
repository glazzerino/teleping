#!/usr/bin/env python3
"""
Simple and secure Telegram API for sending messages to a predetermined user.
"""

import os
import time
import logging
import re
from typing import Optional, Dict, Any
from urllib.parse import quote
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelePing:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_request_time = 0
        self.rate_limit_delay = 1  # 1 second between requests
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate required environment variables."""
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        if not self.chat_id:
            raise ValueError("CHAT_ID not found in environment variables")
        
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', self.bot_token):
            raise ValueError("Invalid bot token format")
        
        if not self.chat_id.isdigit():
            raise ValueError("Invalid chat ID format")
    
    def _sanitize_message(self, text: str) -> str:
        """Sanitize message text for safe transmission."""
        if not isinstance(text, str):
            text = str(text)
        
        # Limit message length (Telegram limit is 4096 characters)
        if len(text) > 4000:
            text = text[:3997] + "..."
        
        # Remove or escape potentially problematic characters
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _rate_limit(self) -> None:
        """Simple rate limiting to avoid hitting API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def send_message(self, text: str, parse_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to the predetermined chat.
        
        Args:
            text: The message text to send
            parse_mode: Optional formatting mode ('HTML' or 'Markdown')
        
        Returns:
            Dict containing success status and response data
        """
        try:
            # Input validation
            if not text or not text.strip():
                return {
                    'success': False,
                    'error': 'Message text cannot be empty'
                }
            
            # Sanitize input
            sanitized_text = self._sanitize_message(text)
            
            # Rate limiting
            self._rate_limit()
            
            # Prepare request data
            data = {
                'chat_id': self.chat_id,
                'text': sanitized_text
            }
            
            if parse_mode and parse_mode in ['HTML', 'Markdown']:
                data['parse_mode'] = parse_mode
            
            # Make API request
            url = f"{self.base_url}/sendMessage"
            response = requests.post(url, data=data, timeout=30)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("Message sent successfully")
                    return {
                        'success': True,
                        'message_id': result.get('result', {}).get('message_id'),
                        'response': result
                    }
                else:
                    error_msg = result.get('description', 'Unknown API error')
                    logger.error(f"API error: {error_msg}")
                    return {
                        'success': False,
                        'error': f"API error: {error_msg}"
                    }
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP error: {response.status_code}"
                }
        
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return {
                'success': False,
                'error': 'Request timeout'
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                'success': False,
                'error': 'Network error'
            }
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': 'Unexpected error occurred'
            }

# Global instance for easy access
_teleping_instance = None

def get_teleping() -> TelePing:
    """Get or create the global TelePing instance."""
    global _teleping_instance
    if _teleping_instance is None:
        _teleping_instance = TelePing()
    return _teleping_instance

def send_message(text: str, parse_mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple function to send a message using the global TelePing instance.
    
    Args:
        text: The message text to send
        parse_mode: Optional formatting mode ('HTML' or 'Markdown')
    
    Returns:
        Dict containing success status and response data
    """
    teleping = get_teleping()
    return teleping.send_message(text, parse_mode)

if __name__ == "__main__":
    # Test the API
    result = send_message("Hello from TelePing! 🚀")
    if result['success']:
        print(f"✅ Message sent successfully! Message ID: {result.get('message_id')}")
    else:
        print(f"❌ Failed to send message: {result.get('error')}")