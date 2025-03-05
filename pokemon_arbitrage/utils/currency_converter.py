"""Currency conversion utilities for Pokemon Card Arbitrage Tool."""

from pokemon_arbitrage.config import CURRENCY_RATES
import logging

logger = logging.getLogger(__name__)

def eur_to_usd(amount):
    """Convert EUR to USD using the configured exchange rate."""
    try:
        return amount * CURRENCY_RATES['EUR_TO_USD']
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to convert EUR to USD: {e}")
        return 0

def gbp_to_usd(amount):
    """Convert GBP to USD using the configured exchange rate."""
    try:
        return amount * CURRENCY_RATES['GBP_TO_USD']
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to convert GBP to USD: {e}")
        return 0

def normalize_currency(price, currency):
    """Normalize any currency to USD."""
    if currency is None or currency.upper() == 'USD':
        return price
    
    conversion_map = {
        'EUR': eur_to_usd,
        'GBP': gbp_to_usd,
        'CAD': lambda x: x * CURRENCY_RATES['CAD_TO_USD']
    }
    
    converter = conversion_map.get(currency.upper())
    if converter:
        return converter(price)
    else:
        logger.warning(f"Unknown currency: {currency}. Returning original price.")
        return price
