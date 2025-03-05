from flask import Flask, request, jsonify, render_template
import os
import requests
import logging
from typing import Dict, List, Any
from dotenv import load_dotenv
import json

# Import config for currency conversion rates
from config import EUR_TO_USD_CONVERSION_RATE, USD_TO_EUR_CONVERSION_RATE, SET_MAPPING

# Import our client modules
from pokemontcg_client import PokemonTCGClient
from price_charting import PriceChartingClient
from card_mapper import CardMapper
from direct_matcher import DirectMatcher

# Add this import at the top
from currency_utils import eur_to_usd, usd_to_eur, process_cardmarket_prices

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('arbitrage.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# API Keys
POKE_API_KEY = os.environ.get('POKE_API_KEY')
PRICECHARTING_API_KEY = os.environ.get('PRICECHARTING_API_KEY')

# Initialize API clients
pokemon_tcg = PokemonTCGClient(POKE_API_KEY)
price_charting = PriceChartingClient(PRICECHARTING_API_KEY)

# Check API keys
if not POKE_API_KEY:
    logger.warning("WARNING: No Pokemon TCG API key found in environment variables! Some functionality may be limited.")
    
if not PRICECHARTING_API_KEY:
    logger.warning("WARNING: No PriceCharting API key found in environment variables! Using simulated pricing data.")

# Core functions without caching
def calculate_profit_margin(buy_price, sell_price):
    """Calculate profit margin percentage"""
    if not buy_price or not sell_price or buy_price <= 0:
        return 0
    return ((sell_price - buy_price) / buy_price) * 100

# Update the calculate_arbitrage function to properly debug all prices considered
def calculate_arbitrage(card_data):
    """Calculate arbitrage opportunities using Near Mint condition when available"""
    try:
        prices = {}
        price_details = {}  # Store detailed information about each price point
        
        # Extract prices from different sources with condition notes
        condition_notes = []
        currency_notes = []
        
        # PriceCharting - typically represents Near Mint ungraded
        if 'price_charting' in card_data:
            if 'loose' in card_data['price_charting'] and card_data['price_charting']['loose'] > 0:
                prices['pricecharting'] = card_data['price_charting']['loose']
                price_details['pricecharting'] = {
                    'source': 'PriceCharting',
                    'condition': 'Ungraded/Near Mint',
                    'original_value': card_data['price_charting']['loose'],
                    'currency': 'USD'
                }
                condition_notes.append("PriceCharting (Ungraded/Near Mint)")
                currency_notes.append("USD")
            # Check for PSA 10 pricing as an alternative
            elif 'psa_grades' in card_data['price_charting'] and 'psa-10' in card_data['price_charting']['psa_grades']:
                prices['pricecharting_psa10'] = card_data['price_charting']['psa-10']
                price_details['pricecharting_psa10'] = {
                    'source': 'PriceCharting',
                    'condition': 'PSA 10',
                    'original_value': card_data['price_charting']['psa-10'],
                    'currency': 'USD'
                }
                condition_notes.append("PriceCharting (PSA 10)")
                currency_notes.append("USD")
            
        # TCGPlayer - prioritize Near Mint condition (high price)
        if 'tcgplayer' in card_data:
            # Log all TCGPlayer prices for debugging
            logger.debug(f"All TCGPlayer prices: {json.dumps(card_data['tcgplayer'])}")
            
            # Check all variants and add them as potential sources
            for variant_key, variant_data in card_data['tcgplayer'].items():
                # Skip non-pricing fields
                if not isinstance(variant_data, dict) or not any(price_type in variant_data for price_type in ['market', 'low', 'mid', 'high']):
                    continue
                    
                # Consider all pricing points
                if 'high' in variant_data and variant_data['high'] > 0:
                    variant_name = f"tcgplayer_{variant_key}_high"
                    prices[variant_name] = variant_data['high']
                    price_details[variant_name] = {
                        'source': 'TCGPlayer',
                        'variant': variant_key,
                        'price_point': 'high (Near Mint)',
                        'original_value': variant_data['high'],
                        'currency': 'USD'
                    }
                
                if 'market' in variant_data and variant_data['market'] > 0:
                    variant_name = f"tcgplayer_{variant_key}_market" 
                    prices[variant_name] = variant_data['market']
                    price_details[variant_name] = {
                        'source': 'TCGPlayer',
                        'variant': variant_key,
                        'price_point': 'market average',
                        'original_value': variant_data['market'],
                        'currency': 'USD'
                    }
            
            # Also add the simplified prices we extracted earlier
            if 'near_mint' in card_data['tcgplayer'] and card_data['tcgplayer']['near_mint'] > 0:
                prices['tcgplayer'] = card_data['tcgplayer']['near_mint']
                price_details['tcgplayer'] = {
                    'source': 'TCGPlayer',
                    'condition': 'Near Mint',
                    'original_value': card_data['tcgplayer']['near_mint'],
                    'currency': 'USD'
                }
                condition_notes.append("TCGPlayer (Near Mint)")
                currency_notes.append("USD")
            elif 'market' in card_data['tcgplayer'] and card_data['tcgplayer']['market'] > 0:
                prices['tcgplayer'] = card_data['tcgplayer']['market']
                price_details['tcgplayer'] = {
                    'source': 'TCGPlayer',
                    'condition': 'Market Average',
                    'original_value': card_data['tcgplayer']['market'],
                    'currency': 'USD'
                }
                condition_notes.append("TCGPlayer (Market Average)")
                currency_notes.append("USD")
            
        # CardMarket - typically represents Near Mint to Excellent condition
        if 'cardmarket' in card_data:
            if 'trendPrice_usd' in card_data['cardmarket'] and card_data['cardmarket']['trendPrice_usd'] > 0:
                prices['cardmarket'] = card_data['cardmarket']['trendPrice_usd']
                price_details['cardmarket'] = {
                    'source': 'CardMarket',
                    'condition': 'Trend/Near Mint',
                    'original_value': card_data['cardmarket']['trendPrice'],
                    'converted_value': card_data['cardmarket']['trendPrice_usd'],
                    'currency': 'EUR→USD',
                    'exchange_rate': EUR_TO_USD_CONVERSION_RATE
                }
                condition_notes.append("CardMarket (Trend/Near Mint)")
                currency_notes.append("EUR→USD")
            elif card_data['cardmarket'].get('trendPrice', 0) > 0:
                prices['cardmarket'] = eur_to_usd(card_data['cardmarket']['trendPrice'])
                price_details['cardmarket'] = {
                    'source': 'CardMarket',
                    'condition': 'Trend/Near Mint',
                    'original_value': card_data['cardmarket']['trendPrice'],
                    'converted_value': prices['cardmarket'],
                    'currency': 'EUR→USD',
                    'exchange_rate': EUR_TO_USD_CONVERSION_RATE
                }
                condition_notes.append("CardMarket (Trend/Near Mint)")
                currency_notes.append("EUR→USD")
        
        # Log all collected prices for debugging
        logger.debug(f"All collected prices: {json.dumps(prices)}")
        
        # Need at least two price sources for arbitrage
        if len(prices) < 2:
            logger.debug(f"Not enough price sources for arbitrage: {len(prices)} sources")
            return None
        
        # Find cheapest and most expensive
        cheapest_source = min(prices.items(), key=lambda x: x[1])
        most_expensive_source = max(prices.items(), key=lambda x: x[1])
        
        # Log the chosen sources
        logger.info(f"Cheapest source: {cheapest_source[0]} = ${cheapest_source[1]:.2f}")
        logger.info(f"Most expensive source: {most_expensive_source[0]} = ${most_expensive_source[1]:.2f}")
        
        # Skip if they're the same source
        if cheapest_source[0] == most_expensive_source[0]:
            logger.debug(f"Same source for cheapest and most expensive: {cheapest_source[0]}")
            return None
        
        # Calculate profit and margin
        buy_price = cheapest_source[1]
        sell_price = most_expensive_source[1]
        
        # Account for fees (simplified)
        sell_fees = {
            'tcgplayer': 0.15,  # 15% fee + shipping (TCGPlayer fee + PayPal fee)
            'tcgplayer_normal_high': 0.15,  # Also apply to variant prices
            'tcgplayer_holofoil_high': 0.15,  # Also apply to variant prices
            'tcgplayer_reverseHolofoil_high': 0.15,  # Also apply to variant prices
            'tcgplayer_normal_market': 0.15,  # Also apply to variant prices
            'tcgplayer_holofoil_market': 0.15,  # Also apply to variant prices
            'tcgplayer_reverseHolofoil_market': 0.15,  # Also apply to variant prices
            'cardmarket': 0.05,  # 5% fee
            'pricecharting': 0.13,  # 13% fee (approximation)
            'pricecharting_psa10': 0.13  # Same fee for PSA 10
        }
        
        # Get fee for the source or default to 10%
        sell_fee_rate = sell_fees.get(most_expensive_source[0], 0.10)
        
        # Shipping costs (simplified)
        shipping_cost = 1.00
        
        # Calculate net sell price after fees
        net_sell_price = sell_price * (1 - sell_fee_rate)
        
        # Calculate profit
        profit = net_sell_price - buy_price - shipping_cost
        profit_margin = (profit / buy_price) * 100 if buy_price > 0 else 0
        
        # Only return if there's a meaningful profit (at least $1 and 10%)
        if profit > 1.0 and profit_margin > 10:
            return {
                'buy_from': cheapest_source[0],
                'buy_source_details': price_details.get(cheapest_source[0], {}),
                'buy_price': buy_price,
                'sell_to': most_expensive_source[0],
                'sell_source_details': price_details.get(most_expensive_source[0], {}),
                'sell_price': sell_price,
                'sell_fee_rate': sell_fee_rate,
                'net_sell_price': net_sell_price,
                'shipping_cost': shipping_cost,
                'profit': profit,
                'profit_margin': profit_margin,
                'condition_notes': condition_notes,
                'currency_notes': currency_notes,
                'exchange_rate': EUR_TO_USD_CONVERSION_RATE,
                'all_prices': price_details  # Include all price details for debugging
            }
        
        logger.debug(f"Profit too small: ${profit:.2f} ({profit_margin:.2f}%)")
        return None
    except Exception as e:
        logger.error(f"Error calculating arbitrage: {str(e)}")
        logger.exception("Full exception details:")
        return None

def generate_test_prices(card):
    """Generate test prices for development/testing"""
    import random
    # Use card number as a seed for consistency
    seed = sum(ord(c) for c in card.get('number', '0'))
    random.seed(seed)
    
    # Generate more realistic test prices based on rarity
    rarity = card.get('rarity', '').lower()
    
    if 'ultra rare' in rarity or 'secret' in rarity:
        base_price = random.uniform(20.0, 150.0)
    elif 'rare holo' in rarity:
        base_price = random.uniform(5.0, 30.0)
    elif 'rare' in rarity:
        base_price = random.uniform(1.0, 10.0)
    else:
        base_price = random.uniform(0.25, 3.0)
    
    # Create a result structure matching the real API
    result = {
        'prices': {
            'loose': round(base_price, 2),
            'graded': round(base_price * 2.5, 2)  # Graded typically more expensive
        },
        'confidence': 1,
        'confidence_label': "Low (Generated)",
        'product_name': f"TEST: {card.get('name')}",
        '_product_id': "test-" + card.get('id', '')
    }
    return result

def get_pricecharting_prices(card_data):
    """Get prices from PriceCharting API with improved matching logic."""
    try:
        card_name = card_data.get('name', 'Unknown')
        set_name = card_data.get('set', 'Unknown')
        card_number = card_data.get('number', '')
        card_id = card_data.get('id', '')
        
        logger.info(f"Fetching PriceCharting data for: {card_name} ({set_name} #{card_number})")
        
        # First check for special direct matches for known problematic cards
        direct_match = DirectMatcher.get_special_match(card_id, PRICECHARTING_API_KEY)
        if direct_match:
            logger.info(f"Found direct match using special matcher for {repr(card_id)}")
            return direct_match
            
        # Special case for known problematic cards like Ditto from Legends Awakened
        set_id = None
        if isinstance(card_data.get('set'), dict):
            set_id = card_data['set'].get('id')
        elif 'set_id' in card_data:
            set_id = card_data['set_id']
        
        # Use set mapping from card_diagnostic.py approach
        if set_id in SET_MAPPING:
            pricecharting_set_name = SET_MAPPING[set_id]["pricecharting_name"]
            logger.info(f"Using mapped set name: {repr(pricecharting_set_name)} for {repr(set_id)}")
        else:
            pricecharting_set_name = set_name
        
        # Try direct lookup with the exact card name, mapped set name, and number
        direct_result = price_charting.direct_card_lookup(
            card_name=card_name,
            set_name=pricecharting_set_name,
            card_number=card_number
        )
        
        if direct_result:
            logger.info("Direct lookup succeeded with mapped set name")
            # Format results to match our expected format
            result = {
                'loose': direct_result.get('prices', {}).get('loose_price', 0),
                'graded': direct_result.get('prices', {}).get('graded_price', 0),
                '_product_id': direct_result.get('product_id', ''),
                '_product_name': direct_result.get('product_name', ''),
                '_match_confidence': direct_result.get('confidence', 3)  # High confidence for direct match
            }
            
            # Extract PSA grades if available
            psa_grades = {}
            prices = direct_result.get('prices', {})
            if 'psa10_price' in prices and prices['psa10_price'] > 0:
                psa_grades['psa-10'] = prices['psa10_price']
            if 'graded_price' in prices and prices['graded_price'] > 0:
                psa_grades['psa-9'] = prices['graded_price']
            if 'grade_8_price' in prices and prices['grade_8_price'] > 0:
                psa_grades['psa-8'] = prices['grade_8_price']
            
            if psa_grades:
                result['psa_grades'] = psa_grades
                
            return result
        
        # Standard flow - use the client's get_card_prices method
        pricing_data = price_charting.get_card_prices(card_data)
        
        # Convert the response to our expected format
        result = {}
        prices = pricing_data.get('prices', {})
        
        if prices:
            result['loose'] = prices.get('loose_price', 0)
            result['graded'] = prices.get('graded_price', 0)
            
            # Add PSA grades if available
            psa_grades = {}
            if 'psa10_price' in prices and prices['psa10_price'] > 0:
                psa_grades['psa-10'] = prices['psa10_price']
            if 'grade_9_price' in prices and prices['grade_9_price'] > 0:
                psa_grades['psa-9'] = prices['grade_9_price']
            if 'grade_8_price' in prices and prices['grade_8_price'] > 0:
                psa_grades['psa-8'] = prices['grade_8_price']
                
            if psa_grades:
                result['psa_grades'] = psa_grades
            
        # Add additional metadata for debugging
        result['_product_id'] = pricing_data.get('product_id', '')
        result['_product_name'] = pricing_data.get('product_name', '')
        result['_match_confidence'] = pricing_data.get('confidence', 0)
        
        # Fix string formatting for potentially problematic values
        loose_price = result.get('loose', 'N/A')
        graded_price = result.get('graded', 'N/A')
        logger.info(f"PriceCharting prices - Loose: ${loose_price}, Graded: ${graded_price}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting PriceCharting prices: {str(e)}")
        return generate_test_prices(card_data)

def extract_tcgplayer_pricing(card_data):
    """Extract and normalize TCGPlayer pricing from Pokemon TCG API response"""
    # Use our new client method for more detailed variant extraction
    return pokemon_tcg.extract_card_variants(card_data)

def get_cardmarket_prices(card_data):
    """Get CardMarket prices from the card data"""
    try:
        cardmarket = card_data.get('cardmarket', {})
        prices = cardmarket.get('prices', {})
        url = cardmarket.get('url', '')
        
        if not prices:
            set_name = card_data.get('set', '').replace(' ', '-').lower()
            name = card_data.get('name', '').replace(' ', '-').lower()
            url = f"https://www.cardmarket.com/en/Pokemon/Products/Singles/{set_name}/{name}"
            return {'prices': {}}, url
        
        # Process all CardMarket prices using our utility function
        processed_prices = process_cardmarket_prices(prices)
        
        return {'prices': processed_prices}, url
    except Exception as e:
        logger.error(f"Error processing CardMarket prices: {str(e)}")
        return {'prices': {}}, ''

# API Routes
@app.route('/')
def index():
    """Serve the main page without raw JSON data"""
    return render_template('index.html')

# Add a new route for initial data that formats it nicely instead of raw JSON
@app.route('/api/initial_data')
def get_initial_data():
    """Get formatted initial data for the homepage"""
    try:
        # Get some basic stats without returning raw JSON
        stats = {
            'exchange_rate': {
                'eur_to_usd': EUR_TO_USD_CONVERSION_RATE,
                'formatted': f"€1.00 = ${EUR_TO_USD_CONVERSION_RATE:.2f}"
            },
            'api_status': {
                'pokemon_tcg': 'Connected' if POKE_API_KEY else 'Not configured',
                'price_charting': 'Connected' if PRICECHARTING_API_KEY else 'Not configured'
            }
        }
        
        return jsonify({
            'stats': stats,
            'welcome_message': 'Welcome to Pokemon Card Arbitrage Tool',
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Error getting initial data: {str(e)}")
        return jsonify({'error': 'Error loading initial data'}), 500

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify({'suggestions': []})
    
    logger.info(f"Searching for cards matching '{query}'...")
    try:
        # Modified query for Pokemon TCG API - remove problematic characters
        safe_query = query.replace("(", "").replace(")", "")
        
        # Use the client for searching
        try:
            cards_data = pokemon_tcg.search_cards(f'name:*{safe_query}*')
            
            suggestions = [
                {
                    'id': card['id'],
                    'name': card['name'],
                    'set': card.get('set', {}).get('name', ''),
                    'number': card.get('number', ''),
                    'image': card.get('images', {}).get('small', '')
                }
                for card in cards_data
            ]
            
            logger.info(f"Found {len(suggestions)} cards matching '{query}'")
            
            return jsonify({'suggestions': suggestions})
        except Exception as e:
            logger.error(f"Error using client, falling back to direct API call: {str(e)}")
            
            # Fallback to direct API call if client fails
            response = requests.get(
                'https://api.pokemontcg.io/v2/cards',
                params={'q': f'name:*{safe_query}*', 'orderBy': 'name', 'pageSize': 15},
                headers={'X-Api-Key': POKE_API_KEY}
            )
            response.raise_for_status()
            
            cards_data = response.json()
            
            suggestions = [
                {
                    'id': card['id'],
                    'name': card['name'],
                    'set': card.get('set', {}).get('name', ''),
                    'number': card.get('number', ''),
                    'image': card.get('images', {}).get('small', '')
                }
                for card in cards_data.get('data', [])
            ]
            
            logger.info(f"Found {len(suggestions)} cards matching '{query}' using fallback")
            
            return jsonify({'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Error searching for '{query}': {str(e)}")
        return jsonify({'error': str(e), 'suggestions': []}), 500

@app.route('/api/card_prices')
def get_card_prices():
    card_id = request.args.get('id', '')
    
    if not card_id:
        return jsonify({'error': 'Card ID is required'}), 400
    
    logger.info(f"Fetching price data for card ID: {card_id}")
    try:
        # Get card data from Pokemon TCG API using our client
        logger.info("Getting card details from Pokemon TCG API...")
        try:
            card_data = pokemon_tcg.get_card(card_id)
        except Exception as e:
            logger.error(f"Error with client, falling back to direct API: {str(e)}")
            # Fallback to direct API call
            response = requests.get(
                f'https://api.pokemontcg.io/v2/cards/{card_id}',
                headers={'X-Api-Key': POKE_API_KEY}
            )
            response.raise_for_status()
            card_data = response.json()['data']
        
        # Extract basic card info
        card = {
            'id': card_data['id'],
            'name': card_data['name'],
            'set': card_data.get('set', {}).get('name', ''),
            'set_id': card_data.get('set', {}).get('id', ''),
            'number': card_data.get('number', ''),
            'rarity': card_data.get('rarity', ''),
            'image': card_data.get('images', {}).get('small', ''),
            'large_image': card_data.get('images', {}).get('large', '')
        }
        
        # Add additional card attributes
        card['printing_type'] = 'Holofoil' if card_data.get('tcgplayer', {}).get('prices', {}).get('holofoil') else 'Normal'
        card['supertype'] = card_data.get('supertype', '')
        card['subtypes'] = card_data.get('subtypes', [])
        
        logger.info(f"Processing card: {card['name']} from {card['set']}")
        
        # Get TCGPlayer prices (with detailed variants)
        logger.info("Extracting TCGPlayer pricing data...")
        tcgplayer_prices, tcgplayer_url = extract_tcgplayer_pricing(card_data)
        
        # Get PriceCharting prices with improved matching logic
        logger.info("Fetching PriceCharting pricing data...")
        pc_result = get_pricecharting_prices(card_data)
        
        # Get CardMarket prices
        logger.info("Processing CardMarket pricing data...")
        cm_result, cm_url = get_cardmarket_prices(card_data)
        
        # Combine all data
        result = {
            **card,
            'tcgplayer': tcgplayer_prices,
            'tcgplayer_url': tcgplayer_url,
            'price_charting': pc_result,
            'pricecharting_url': f"https://www.pricecharting.com/search-products?q={card['name']} {card['set']}",
            'cardmarket': cm_result.get('prices', {}),
            'cardmarket_url': cm_url,
            'currency_info': {
                'eur_to_usd_rate': EUR_TO_USD_CONVERSION_RATE,
                'usd_to_eur_rate': USD_TO_EUR_CONVERSION_RATE,
                'base_currency': 'USD'  # Arbitrage calculations are in USD
            }
        }
        
        # Calculate arbitrage opportunities
        logger.info("Calculating arbitrage opportunities...")
        result['arbitrage'] = calculate_arbitrage(result)
        
        if result['arbitrage']:
            buy_price = result['arbitrage']['buy_price']
            sell_price = result['arbitrage']['sell_price']
            profit = result['arbitrage']['profit']
            profit_margin = result['arbitrage']['profit_margin']
            logger.info(f"Found arbitrage opportunity! Buy: ${buy_price:.2f} Sell: ${sell_price:.2f} Profit: ${profit:.2f} ({profit_margin:.2f}%)")
        else:
            logger.info("No profitable arbitrage opportunities found")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting card prices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sets')
def get_sets():
    logger.info("Fetching all Pokemon card sets...")
    try:
        # Use the client for getting sets
        try:
            sets_data = pokemon_tcg.get_sets()
            
            # Format the sets
            sets = []
            for s in sets_data:
                sets.append({
                    'id': s['id'],
                    'name': s['name'],
                    'series': s['series'],
                    'releaseDate': s['releaseDate'],
                    'imageUrl': s.get('images', {}).get('symbol', '')
                })
                
            # Sort by release date (newest first)
            sets.sort(key=lambda x: x['releaseDate'], reverse=True)
            
            logger.info(f"Found {len(sets)} Pokemon card sets")
            
            return jsonify({'sets': sets})
        except Exception as e:
            logger.error(f"Error using client, falling back to direct API call: {str(e)}")
            
            # Fallback to direct API calls
            response = requests.get('https://api.pokemontcg.io/v2/sets', 
                                  headers={'X-Api-Key': POKE_API_KEY})
            
            # Check for rate limiting
            if response.status_code == 429:
                logger.warning("Rate limit hit for Pokemon TCG API")
                return jsonify({'error': 'API rate limit exceeded. Please try again later.'}), 429
                
            response.raise_for_status()
            
            sets_data = response.json()
            
            # Format the sets
            sets = []
            for s in sets_data['data']:
                sets.append({
                    'id': s['id'],
                    'name': s['name'],
                    'series': s['series'],
                    'releaseDate': s['releaseDate'],
                    'imageUrl': s.get('images', {}).get('symbol', '')
                })
            
            # Sort by release date (newest first)
            sets.sort(key=lambda x: x['releaseDate'], reverse=True)
            
            logger.info(f"Found {len(sets)} Pokemon card sets")
            
            return jsonify({'sets': sets})
    except Exception as e:
        logger.error(f"Error fetching sets: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Print banner
    print("\n" + "="*80)
    print(" 🃏  POKEMON CARD ARBITRAGE TOOL  🃏 ".center(80))
    print("="*80)
    print("\nStarting server...")
    
    # Print API key status
    if POKE_API_KEY:
        print("✅ Pokemon TCG API key found")
    else:
        print("❌ No Pokemon TCG API key found! Some functionality may be limited.")
        
    if PRICECHARTING_API_KEY:
        print("✅ PriceCharting API key found")
    else:
        print("⚠️  No PriceCharting API key found. Using simulated pricing data.")
    
    print("\n📊 Starting web interface...")
    print("🌐 Access the tool in your browser at: http://127.0.0.1:5000")
    print("\n📊 Session Log:")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
