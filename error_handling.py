
"""
Error handling utilities for the Pokemon Store Tools and Modules
"""

import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

class ApiRateLimitError(Exception):
    """Exception raised when an API rate limit is hit"""
    pass

class ApiResponseError(Exception):
    """Exception raised for general API errors"""
    pass

def retry_with_backoff(max_retries=3, backoff_factor=1.5):
    """
    Retry decorator with exponential backoff for API calls
    
    Args:
        max_retries: Maximum number of retries
        backoff_factor: Multiplicative factor for backoff time
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            backoff_time = 1  # Start with 1 second
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except ApiRateLimitError:
                    wait_time = backoff_time * (backoff_factor ** retries)
                    logger.warning(f"Rate limit hit. Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                    raise
            
            # If we've exhausted retries
            logger.error(f"Max retries ({max_retries}) exceeded in {func.__name__}")
            raise ApiResponseError(f"Maximum retries exceeded")
                
        return wrapper
    return decorator

def handle_api_response(response, cache_key=None, get_cached_data_func=None):
    """
    Handle API responses with proper error handling and rate limit checking
    
    Args:
        response: The requests response object
        cache_key: Optional cache key to retrieve cached data if rate limited
        get_cached_data_func: Function to get cached data if needed
    """
    if response.status_code == 200:
        return response.json()
    
    if response.status_code == 429:  # Rate limit
        logger.warning(f"API rate limit exceeded: {response.text}")
        
        # Try to use cached data if available
        if cache_key and get_cached_data_func:
            logger.info(f"Attempting to use cached data for {cache_key}")
            cached_data = get_cached_data_func(cache_key, max_age_hours=720)  # 30 days
            if cached_data:
                return cached_data
                
        raise ApiRateLimitError("API rate limit exceeded")
        
    # Handle other errors
    logger.error(f"API error: {response.status_code} - {response.text}")
    response.raise_for_status()
