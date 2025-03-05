"""Price validation utilities for Pokemon Card Arbitrage Tool."""

import logging

logger = logging.getLogger(__name__)

# Common price constants
TYPICAL_MAX_PRICE = {
    "common": 2.0,      # Typical max for common cards
    "uncommon": 5.0,    # Typical max for uncommon cards
    "rare": 20.0,       # Typical max for regular rares
    "holofoil": 50.0,   # Typical max for regular holos
    "ultra_rare": 200.0, # Typical max for ultra rares (GX, V, etc)
    "secret_rare": 500.0, # Typical max for secret rares
    "promo": 100.0,     # Typical max for promos
    "default": 1000.0   # Default max threshold
}

# Known placeholder values in various marketplaces
PLACEHOLDER_VALUES = [
    999.99,  # Common placeholder for out-of-stock
    9999.99, # Another placeholder
    0.01,    # Placeholder for "make offer"
    0.99     # Sometimes used as a placeholder
]

# Define price types that should never be used for arbitrage calculations
INVALID_PRICE_TYPES = ['high']

def detect_placeholder_price(price):
    """
    Detect if a price is likely a placeholder value
    
    Args:
        price (float): Price to check
        
    Returns:
        bool: True if the price is likely a placeholder
    """
    for placeholder in PLACEHOLDER_VALUES:
        if abs(price - placeholder) < 0.01:
            return True
    return False

def validate_price_source(source_info):
    """
    Validate if a price source is acceptable for arbitrage calculations
    
    Args:
        source_info (dict): Information about the price source
        
    Returns:
        bool: True if the source is valid for arbitrage, False otherwise
    """
    # Check if the price type is in the invalid list
    if 'price_type' in source_info and source_info['price_type'] in INVALID_PRICE_TYPES:
        logger.warning(f"Invalid price type detected: {source_info['price_type']}")
        return False
        
    return True

def validate_price_pair(buy_price, sell_price, buy_source=None, sell_source=None):
    """
    Validate if a buy/sell price pair is realistic for arbitrage
    
    Args:
        buy_price (float): Buy price
        sell_price (float): Sell price
        buy_source (str, optional): Source of buy price
        sell_source (str, optional): Source of sell price
        
    Returns:
        bool: True if the price pair seems valid for arbitrage
    """
    # Basic validations
    if buy_price <= 0 or sell_price <= 0:
        return False
    
    # Check for placeholders
    if detect_placeholder_price(buy_price) or detect_placeholder_price(sell_price):
        logger.warning(f"Detected placeholder price: buy=${buy_price:.2f}, sell=${sell_price:.2f}")
        return False
    
    # Check if profit margin is suspiciously high
    if buy_price < 0.5 and sell_price > 50:
        logger.warning(f"Suspicious high differential: ${buy_price:.2f} ({buy_source}) → ${sell_price:.2f} ({sell_source})")
        return False
        
    # Calculate profit margin
    profit = sell_price - buy_price
    margin = (profit / buy_price) * 100
    
    # Reject unrealistic margins
    if margin > 500:  # 500% profit margin
        logger.warning(f"Unrealistic profit margin: {margin:.2f}% (${buy_price:.2f} → ${sell_price:.2f})")
        return False
        
    return True

def validate_card_price(price, card_data=None):
    """
    Validate if a price seems reasonable based on the card's information
    
    Args:
        price (float): Price to validate
        card_data (dict, optional): Card data with rarity info
        
    Returns:
        bool: True if the price seems valid
    """
    if price <= 0:
        return False
        
    # Detect placeholders
    if detect_placeholder_price(price):
        return False
    
    # Use card rarity to determine reasonable price ceiling if available
    if card_data and 'rarity' in card_data:
        rarity_lower = card_data['rarity'].lower()
        
        # Determine card type category
        if 'common' in rarity_lower:
            max_price = TYPICAL_MAX_PRICE['common']
        elif 'uncommon' in rarity_lower:
            max_price = TYPICAL_MAX_PRICE['uncommon']
        elif 'rare' in rarity_lower and 'holo' in rarity_lower:
            max_price = TYPICAL_MAX_PRICE['holofoil']
        elif 'rare' in rarity_lower:
            max_price = TYPICAL_MAX_PRICE['rare']
        elif any(x in rarity_lower for x in ['ultra', 'secret', 'hyper']):
            max_price = TYPICAL_MAX_PRICE['secret_rare']
        elif 'promo' in rarity_lower:
            max_price = TYPICAL_MAX_PRICE['promo']
        else:
            max_price = TYPICAL_MAX_PRICE['default']
        
        # If price exceeds the typical max by a large margin, it's suspicious
        if price > max_price * 3:
            logger.warning(f"Price ${price:.2f} is unusually high for {rarity_lower} card")
            return False
    
    # Default case - use the global maximum
    return price < TYPICAL_MAX_PRICE['default']
