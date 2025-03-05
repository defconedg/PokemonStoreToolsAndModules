"""Core arbitrage calculation logic for Pokemon Card Arbitrage Tool."""

import logging
from pokemon_arbitrage.config import MIN_PROFIT_AMOUNT, MIN_PROFIT_PERCENTAGE
from pokemon_arbitrage.core.price_extractor import extract_all_prices

logger = logging.getLogger(__name__)

# Add price sanity check constants
MAX_REASONABLE_PRICE = 1000.0
MAX_PRICE_DIFFERENTIAL = 500.0
SUSPICIOUS_LOW_BUY = 0.25
SUSPICIOUS_HIGH_SELL = 500.0

# Define which variants can be compared (same card, different printing)
COMPARABLE_VARIANTS = {
    'normal': ['normal', 'standard'],
    'holofoil': ['holofoil'],
    'reverseHolofoil': ['reverseHolofoil'],
    '1stEdition': ['1stEdition'],
    'unlimited': ['unlimited'],
    'standard': ['standard', 'normal'],
}

# Define which price types are reliable (HIGH is NOT reliable)
RELIABLE_PRICE_TYPES = ['market', 'trend', 'average', 'mid', 'directLow', 'loose-price']
UNRELIABLE_PRICE_TYPES = ['high']  # Explicitly blocked

def are_variants_comparable(variant1, variant2):
    """Check if two card variants can be reasonably compared."""
    # Normalize variant names
    v1 = variant1.lower() if isinstance(variant1, str) else 'standard'
    v2 = variant2.lower() if isinstance(variant2, str) else 'standard'
    
    # Exact match is always comparable
    if v1 == v2:
        return True
    
    # Check if variants are in each other's compatibility lists
    for base_variant, compatible_list in COMPARABLE_VARIANTS.items():
        if v1 == base_variant.lower():
            return v2 in [v.lower() for v in compatible_list]
        if v2 == base_variant.lower():
            return v1 in [v.lower() for v in compatible_list]
    
    return False

def calculate_arbitrage_opportunities(card_data):
    """Calculate all possible arbitrage opportunities for a card."""
    try:
        # Extract normalized price data from all sources
        all_prices = extract_all_prices(card_data)
        
        # Need at least two prices for comparison
        if len(all_prices) < 2:
            logger.info("Not enough price points to calculate arbitrage")
            return []
        
        # Log all extracted prices for debugging
        logger.debug(f"Extracted {len(all_prices)} price points for {card_data.get('name', 'Unknown')}")
        for price in all_prices:
            logger.debug(f"- {price['source']} {price['variant']} {price['price_type']}: ${price['price']:.2f}")
        
        # Find all possible arbitrage opportunities
        opportunities = []
        
        for buy_option in all_prices:
            for sell_option in all_prices:
                # Skip if same source/variant combination
                if buy_option['source'] == sell_option['source'] and buy_option['variant'] == sell_option['variant']:
                    continue
                
                # CRITICAL FIX 1: Don't compare different variants (e.g., holo vs non-holo)
                if not are_variants_comparable(buy_option['variant'], sell_option['variant']):
                    logger.debug(f"Skipping non-comparable variants: {buy_option['variant']} vs {sell_option['variant']}")
                    continue
                
                # CRITICAL FIX 2: Skip unreliable price types (especially "high" prices)
                if buy_option['price_type'] in UNRELIABLE_PRICE_TYPES or sell_option['price_type'] in UNRELIABLE_PRICE_TYPES:
                    logger.warning(f"Skipping unreliable price type: buy={buy_option['price_type']}, sell={sell_option['price_type']}")
                    continue
                
                # Only use price types that are considered reliable
                if buy_option['price_type'] not in RELIABLE_PRICE_TYPES or sell_option['price_type'] not in RELIABLE_PRICE_TYPES:
                    logger.debug(f"Skipping non-recommended price types: buy={buy_option['price_type']}, sell={sell_option['price_type']}")
                    continue
                
                # Calculate real costs with shipping and fees included
                buy_cost = buy_option['buy_price_with_shipping']
                sell_revenue = sell_option['sell_price_after_fees']
                
                # Calculate profit and margin
                profit = sell_revenue - buy_cost
                profit_margin = (profit / buy_cost) * 100 if buy_cost > 0 else 0
                
                # Price sanity checks - skip unrealistic opportunities
                # Skip extremely high prices that are likely errors
                if sell_option['price'] > MAX_REASONABLE_PRICE:
                    logger.warning(f"Skipping suspiciously high price: ${sell_option['price']:.2f} from {sell_option['source']}")
                    continue
                
                # Skip suspicious price differentials (very low buy, very high sell)
                if buy_option['price'] < SUSPICIOUS_LOW_BUY and sell_option['price'] > SUSPICIOUS_HIGH_SELL:
                    logger.warning(
                        f"Skipping suspicious price differential: ${buy_option['price']:.2f} ({buy_option['source']}) → "
                        f"${sell_option['price']:.2f} ({sell_option['source']})"
                    )
                    continue
                
                # Skip unrealistic profit margins
                if profit_margin > MAX_PRICE_DIFFERENTIAL:
                    logger.warning(f"Skipping unrealistic profit margin: {profit_margin:.2f}% for {card_data.get('name', 'Unknown Card')}")
                    continue
                
                # Only consider meaningful profit
                if profit > MIN_PROFIT_AMOUNT and profit_margin > MIN_PROFIT_PERCENTAGE:
                    opportunities.append({
                        'buy_from': {
                            'source': buy_option['source'],
                            'variant': buy_option['variant'],
                            'price_type': buy_option['price_type'],
                            'condition': buy_option['condition']
                        },
                        'buy_price': buy_option['price'],
                        'sell_to': {
                            'source': sell_option['source'],
                            'variant': sell_option['variant'],
                            'price_type': sell_option['price_type'],
                            'condition': sell_option['condition']
                        },
                        'sell_price': sell_option['price'],
                        'profit': round(profit, 2),
                        'profit_margin': round(profit_margin, 2),
                        # Add variant info for reference
                        'variant_info': f"{buy_option['variant']} to {sell_option['variant']}",
                    })
        
        # Sort opportunities by profit margin
        if opportunities:
            opportunities.sort(key=lambda x: x['profit_margin'], reverse=True)
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error calculating arbitrage: {str(e)}")
        return []
