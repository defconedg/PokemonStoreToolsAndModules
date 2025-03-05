"""
Utility functions for currency conversion in Pokemon Card Arbitrage Tool
"""
import logging
from typing import Dict, Any, Union, Optional

from config import EUR_TO_USD_CONVERSION_RATE, USD_TO_EUR_CONVERSION_RATE

logger = logging.getLogger(__name__)

def eur_to_usd(amount: Union[float, int]) -> float:
    """Convert EUR amount to USD using current exchange rate from config"""
    if amount is None:
        return 0.0
    try:
        usd_amount = float(amount) * EUR_TO_USD_CONVERSION_RATE
        logger.debug(f"Currency conversion: €{amount:.2f} → ${usd_amount:.2f} (rate: {EUR_TO_USD_CONVERSION_RATE})")
        return usd_amount
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting EUR to USD: {e} (value: {amount})")
        return 0.0

def usd_to_eur(amount: Union[float, int]) -> float:
    """Convert USD amount to EUR using current exchange rate from config"""
    if amount is None:
        return 0.0
    try:
        eur_amount = float(amount) * USD_TO_EUR_CONVERSION_RATE
        logger.debug(f"Currency conversion: ${amount:.2f} → €{eur_amount:.2f} (rate: {USD_TO_EUR_CONVERSION_RATE})")
        return eur_amount
    except (ValueError, TypeError) as e:
        logger.error(f"Error converting USD to EUR: {e} (value: {amount})")
        return 0.0

def process_cardmarket_prices(prices: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process CardMarket prices to add USD conversions and metadata
    
    Args:
        prices: Raw CardMarket prices dictionary
        
    Returns:
        Enhanced prices dictionary with conversions
    """
    result = prices.copy()
    
    # Add conversion metadata
    result['_currency'] = 'EUR'
    result['_exchange_rate'] = EUR_TO_USD_CONVERSION_RATE
    
    # Convert main prices
    for price_key in ['trendPrice', 'lowPrice', 'avg1', 'avg7', 'avg30']:
        if price_key in result and result[price_key] is not None:
            usd_key = f"{price_key}_usd"
            result[usd_key] = eur_to_usd(result[price_key])
    
    return result
