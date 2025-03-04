
"""
Utility functions for the Pokemon Store Tools and Modules
"""

import os
import json
import time
import logging
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

# Currency conversion utilities
def eur_to_usd(eur_amount, exchange_rate=1.1):
    """Convert EUR to USD with a given exchange rate"""
    if not eur_amount:
        return 0
    
    # Use Decimal for more accurate financial calculations
    return float(Decimal(str(eur_amount)) * Decimal(str(exchange_rate)))

def format_price(price, decimal_places=2):
    """Format a price with proper rounding"""
    if not price:
        return None
        
    # Use Decimal for proper financial rounding
    decimal_price = Decimal(str(price))
    return float(decimal_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# Enhanced caching utilities
class EnhancedCache:
    """Enhanced caching implementation with more features"""
    
    def __init__(self, cache_dir):
        """Initialize the cache with a directory"""
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
    def get(self, cache_key, max_age_hours=24):
        """Get data from cache if not expired"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < max_age_hours * 3600:
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted cache file {cache_file}")
                    return None
                except Exception as e:
                    logger.error(f"Error reading cache file {cache_file}: {str(e)}")
                    return None
        
        return None
        
    def save(self, cache_key, data):
        """Save data to cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving to cache {cache_file}: {str(e)}")
            return False
            
    def invalidate(self, cache_key):
        """Invalidate a specific cache entry"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                return True
            except Exception as e:
                logger.error(f"Error removing cache file {cache_file}: {str(e)}")
                return False
        return False
        
    def clear_all(self, older_than_hours=None):
        """Clear all cache or only entries older than specified hours"""
        count = 0
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(self.cache_dir, filename)
            if older_than_hours:
                file_age = time.time() - os.path.getmtime(filepath)
                if file_age < older_than_hours * 3600:
                    continue
                    
            try:
                os.remove(filepath)
                count += 1
            except Exception as e:
                logger.error(f"Error removing cache file {filepath}: {str(e)}")
                
        return count

# Market fee calculator
def calculate_selling_fees(market, price):
    """
    Calculate selling fees for different marketplaces
    
    Args:
        market: Marketplace name (tcgplayer, cardmarket, pricecharting)
        price: The selling price
        
    Returns:
        net_price: Price after fees
        fee_amount: Amount taken by fees
    """
    fee_rates = {
        'tcgplayer': 0.15,  # 15% fee (includes PayPal fees)
        'cardmarket': 0.05,  # 5% fee 
        'pricecharting': 0.13,  # 13% fee (approximation)
        'ebay': 0.1325,  # 13.25% fee (approximation)
    }
    
    fee_rate = fee_rates.get(market.lower(), 0.10)  # Default to 10%
    fee_amount = price * fee_rate
    net_price = price - fee_amount
    
    return net_price, fee_amount
