"""Extract and normalize price data from different sources."""

import logging
import json
from pokemon_arbitrage.config import CONDITION_MAPPING, MARKETPLACE_FEES, SHIPPING_COSTS
from pokemon_arbitrage.utils.currency_converter import normalize_currency

logger = logging.getLogger(__name__)

# Add constants for price validation
MIN_VALID_PRICE = 0.01
MAX_VALID_PRICE = 1000.0

# Known placeholder values that should be rejected
PLACEHOLDER_VALUES = [999.99, 9999.99, 0.01]

def normalize_variant_name(variant):
    """Standardize variant names across different platforms."""
    if not variant:
        return 'normal'
        
    variant_lower = variant.lower()
    
    # Map common variant names to standardized ones
    if 'holo' in variant_lower and 'reverse' in variant_lower:
        return 'reverseHolofoil'
    elif 'holo' in variant_lower and '1st' in variant_lower:
        return '1stEditionHolofoil'
    elif 'holo' in variant_lower:
        return 'holofoil'
    elif '1st' in variant_lower:
        return '1stEdition'
    elif 'unlimited' in variant_lower:
        return 'unlimited'
    else:
        return 'normal'

def is_valid_price(price, source=None):
    """Check if price is valid and not a placeholder or error."""
    if price is None or not isinstance(price, (int, float)) or price <= 0:
        return False
    
    # Reject common placeholder values
    for placeholder in PLACEHOLDER_VALUES:
        if abs(price - placeholder) < 0.01:
            if source:
                logger.warning(f"Detected placeholder price ${placeholder} from {source}")
            return False
    
    # Reject unreasonably high prices
    if price > MAX_VALID_PRICE:
        if source:
            logger.warning(f"Rejecting suspiciously high price ${price:.2f} from {source}")
        return False
    
    return True

def extract_tcgplayer_prices(tcg_data):
    """Extract structured price data from TCGPlayer API response."""
    prices = []
    
    if not tcg_data or not isinstance(tcg_data, dict):
        return prices
    
    for variant_key, variant_data in tcg_data.items():
        if not isinstance(variant_data, dict):
            continue
            
        # Normalize the variant name - CRITICAL FIX
        normalized_variant = normalize_variant_name(variant_key)
        
        # Extract price points - CRITICAL FIX: EXCLUDE "high" price
        price_points = [
            ('market', 'Market Average'),
            ('low', 'Low'),
            ('mid', 'Mid'),
            ('directLow', 'Direct Low')
            # "high" is completely removed - don't even extract it
        ]
        
        for price_key, condition in price_points:
            if price_key in variant_data and variant_data[price_key]:
                price = variant_data[price_key]
                
                # Skip invalid prices
                if not is_valid_price(price, f"tcgplayer-{variant_key}-{price_key}"):
                    continue
                
                # TCGPlayer prices typically assume Near Mint
                standard_condition = CONDITION_MAPPING.get('Near Mint')
                
                prices.append({
                    'source': 'tcgplayer',
                    'variant': normalized_variant,  # Use normalized variant name
                    'price_type': price_key,
                    'condition': standard_condition,
                    'raw_condition': condition,
                    'price': price,
                    'currency': 'USD',
                    'fee_rate': MARKETPLACE_FEES['tcgplayer'],
                    'sell_price_after_fees': price * (1 - MARKETPLACE_FEES['tcgplayer']),
                    'buy_price_with_shipping': price + SHIPPING_COSTS['domestic']
                })
    
    return prices

def extract_cardmarket_prices(cardmarket_data):
    """Extract structured price data from CardMarket API response."""
    prices = []
    
    if not cardmarket_data or not isinstance(cardmarket_data, dict):
        return prices
    
    # Process trend price
    if 'trendPrice' in cardmarket_data and is_valid_price(cardmarket_data['trendPrice'], "cardmarket-trend"):
        eur_price = cardmarket_data['trendPrice']
        usd_price = normalize_currency(eur_price, 'EUR')
        
        prices.append({
            'source': 'cardmarket',
            'variant': 'standard',  # CardMarket standard is comparable to normal
            'price_type': 'trend',
            'condition': CONDITION_MAPPING.get('Near Mint'),  # CardMarket trend assumes NM
            'price': usd_price,
            'original_price': eur_price,
            'currency': 'USD',
            'original_currency': 'EUR',
            'fee_rate': MARKETPLACE_FEES['cardmarket'],
            'sell_price_after_fees': usd_price * (1 - MARKETPLACE_FEES['cardmarket']),
            'buy_price_with_shipping': usd_price + SHIPPING_COSTS['international']
        })
        
    # Process average price if available
    if 'averagePrice' in cardmarket_data and is_valid_price(cardmarket_data['averagePrice'], "cardmarket-average"):
        eur_price = cardmarket_data['averagePrice']
        usd_price = normalize_currency(eur_price, 'EUR')
        
        prices.append({
            'source': 'cardmarket',
            'variant': 'standard',
            'price_type': 'average',
            'condition': CONDITION_MAPPING.get('Near Mint'),
            'price': usd_price,
            'original_price': eur_price,
            'currency': 'USD',
            'original_currency': 'EUR',
            'fee_rate': MARKETPLACE_FEES['cardmarket'],
            'sell_price_after_fees': usd_price * (1 - MARKETPLACE_FEES['cardmarket']),
            'buy_price_with_shipping': usd_price + SHIPPING_COSTS['international']
        })
    
    return prices

def extract_pricecharting_prices(pricecharting_data):
    """Extract structured price data from PriceCharting API response."""
    prices = []
    
    if not pricecharting_data or not isinstance(pricecharting_data, dict):
        logger.warning("Invalid or missing PriceCharting data")
        return prices
    
    # Add a check for error responses from PriceCharting
    if 'status' in pricecharting_data and pricecharting_data['status'] == 'error':
        logger.error(f"PriceCharting API error: {pricecharting_data.get('error', 'Unknown error')}")
        return prices
    
    # Map PriceCharting price types to conditions
    price_types = [
        ('loose-price', CONDITION_MAPPING.get('Near Mint')),
        ('cib-price', 'Complete In Box'),
        ('new-price', 'Sealed')
    ]
    
    # Detect variant from product name - CRITICAL FIX
    product_name = pricecharting_data.get('product-name', '').lower()
    if 'holo' in product_name and 'reverse' in product_name:
        variant = 'reverseHolofoil'
    elif 'holo' in product_name or 'holofoil' in product_name:
        variant = 'holofoil'
    elif '1st edition' in product_name:
        variant = '1stEdition'
    else:
        variant = 'normal'
    
    for price_key, condition in price_types:
        if price_key in pricecharting_data:
            # PriceCharting prices are in cents
            price_cents = pricecharting_data[price_key]
            
            # Convert to dollars
            try:
                if price_cents is not None:
                    price = float(price_cents) / 100.0
                else:
                    continue
            except (ValueError, TypeError):
                logger.warning(f"Invalid price value from PriceCharting: {price_cents}")
                continue
                
            # Skip invalid prices
            if not is_valid_price(price, f"pricecharting-{price_key}"):
                continue
            
            prices.append({
                'source': 'pricecharting',
                'variant': variant,  # Include variant information
                'price_type': price_key,
                'condition': condition,
                'price': price,
                'currency': 'USD',
                'fee_rate': MARKETPLACE_FEES['pricecharting'],
                'sell_price_after_fees': price * (1 - MARKETPLACE_FEES['pricecharting']),
                'buy_price_with_shipping': price + SHIPPING_COSTS['domestic']
            })
    
    return prices

def extract_all_prices(card_data):
    """Extract all prices from different sources into a standardized format."""
    all_prices = []
    
    try:
        # TCGPlayer prices
        if 'tcgplayer' in card_data:
            tcg_prices = extract_tcgplayer_prices(card_data['tcgplayer'])
            all_prices.extend(tcg_prices)
            logger.debug(f"Extracted {len(tcg_prices)} TCGPlayer prices")
        
        # CardMarket prices
        if 'cardmarket' in card_data:
            cardmarket_prices = extract_cardmarket_prices(card_data['cardmarket'])
            all_prices.extend(cardmarket_prices)
            logger.debug(f"Extracted {len(cardmarket_prices)} CardMarket prices")
        
        # PriceCharting prices
        if 'price_charting' in card_data:
            try:
                pricecharting_prices = extract_pricecharting_prices(card_data['price_charting'])
                all_prices.extend(pricecharting_prices)
                logger.debug(f"Extracted {len(pricecharting_prices)} PriceCharting prices")
            except Exception as e:
                logger.error(f"Error extracting PriceCharting prices: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting prices: {str(e)}")
    
    # Log variant and price type information
    if all_prices:
        variants = {p['variant'] for p in all_prices}
        price_types = {p['price_type'] for p in all_prices}
        
        logger.info(f"Extracted {len(all_prices)} prices from all sources")
        logger.info(f"Found {len(variants)} card variants: {', '.join(variants)}")
        logger.info(f"Found price types: {', '.join(price_types)}")
        
    return all_prices
