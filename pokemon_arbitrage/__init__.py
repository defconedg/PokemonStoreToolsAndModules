"""Pokemon Card Arbitrage Tool.

A tool for identifying arbitrage opportunities in the Pokemon TCG market.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Import core functionality
from pokemon_arbitrage.core import calculate_arbitrage_opportunities, get_best_arbitrage_opportunity
