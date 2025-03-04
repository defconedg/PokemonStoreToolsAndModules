from flask import Flask, request, jsonify, render_template
import os
import time
import json
import requests
import logging
from threading import Thread
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

# Import config for currency conversion rates
from config import EUR_TO_USD_CONVERSION_RATE, USD_TO_EUR_CONVERSION_RATE

# Import our new client modules
from pokemontcg_client import PokemonTCGClient
from price_charting import PriceChartingClient

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

# Cache setup
cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
    logger.info("Created cache directory: {}".format(cache_dir))

def get_cached_data(cache_key, max_age_hours=24):
    """Get data from cache if not expired"""
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")
    
    if os.path.exists(cache_file):
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age < max_age_hours * 3600:
            logger.debug(f"Cache hit: {cache_key}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        else:
            logger.debug(f"Cache expired: {cache_key}")
    else:
        logger.debug(f"Cache miss: {cache_key}")
    
    return None

def save_to_cache(cache_key, data):
    """Save data to cache"""
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.debug(f"Saved to cache: {cache_key}")

def calculate_profit_margin(buy_price, sell_price):
    """Calculate profit margin percentage"""
    if not buy_price or not sell_price or buy_price <= 0:
        return 0
    return ((sell_price - buy_price) / buy_price) * 100

def calculate_arbitrage(card_data):
    """Calculate arbitrage opportunities"""
    try:
        prices = {}
        
        # Extract prices from different sources
        if 'price_charting' in card_data and 'loose' in card_data['price_charting']:
            prices['pricecharting'] = card_data['price_charting']['loose']
            
        if 'tcgplayer' in card_data and 'market' in card_data['tcgplayer']:
            prices['tcgplayer'] = card_data['tcgplayer']['market']
            
        if 'cardmarket' in card_data and 'trendPrice' in card_data['cardmarket']:
            # Use USD-converted price if available
            if 'trendPrice_usd' in card_data['cardmarket']:
                prices['cardmarket'] = card_data['cardmarket']['trendPrice_usd']
            else:
                # Use the configured exchange rate
                prices['cardmarket'] = card_data['cardmarket']['trendPrice'] * EUR_TO_USD_CONVERSION_RATE
        
        # Need at least two price sources for arbitrage
        if len(prices) < 2:
            return None
        
        # Find cheapest and most expensive
        cheapest_source = min(prices.items(), key=lambda x: x[1])
        most_expensive_source = max(prices.items(), key=lambda x: x[1])
        
        # Calculate profit and margin
        buy_price = cheapest_source[1]
        sell_price = most_expensive_source[1]
        
        # Account for fees (simplified)
        sell_fees = {
            'tcgplayer': 0.15,  # 15% fee + shipping (TCGPlayer fee + PayPal fee)
            'cardmarket': 0.05,  # 5% fee
            'pricecharting': 0.13  # 13% fee (approximation)
        }
        
        # Shipping costs (simplified)
        shipping_cost = 1.00
        
        # Calculate net sell price after fees
        net_sell_price = sell_price * (1 - sell_fees.get(most_expensive_source[0], 0.10))
        
        # Calculate profit
        profit = net_sell_price - buy_price - shipping_cost
        
        # Only return if there's a profit
        if profit > 0:
            return {
                'buy_from': cheapest_source[0],
                'buy_price': buy_price,
                'sell_to': most_expensive_source[0],
                'sell_price': sell_price,
                'net_sell_price': net_sell_price,
                'profit': profit,
                'profit_margin': (profit / buy_price) * 100
            }
        
        return None
    except Exception as e:
        logger.error(f"Error calculating arbitrage: {str(e)}")
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
    
    pricing_data = {
        'prices': {
            'loose': round(base_price, 2),
            'graded': round(base_price * 2.5, 2)  # Graded typically more expensive
        }
    }
    return pricing_data

def get_pricecharting_prices(card_data):
    """Get prices from PriceCharting API."""
    try:
        logger.info("Fetching PriceCharting data for: {}".format(card_data.get('name')))
        
        # Use the improved method with full card data for better accuracy
        pricing_data = price_charting.get_card_prices_by_tcgdata(card_data)
        
        # Log selected product for verification
        if 'product' in pricing_data:
            product_name = pricing_data['product'].get('name', 'Unknown')
            logger.info(f"Matched with PriceCharting product: {product_name}")
            
            # Remove product info before returning (not needed in frontend)
            pricing_data.pop('product', None)
            
        logger.info("PriceCharting prices - Loose: ${}, Graded: ${}".format(
            pricing_data['prices'].get('loose', 'N/A'), 
            pricing_data['prices'].get('graded', 'N/A')
        ))
        
        # Add additional logging for graded variants if available
        if 'graded_variants' in pricing_data['prices']:
            grade_info = ", ".join([f"{k}: ${v}" for k, v in pricing_data['prices']['graded_variants'].items()])
            logger.debug(f"Graded variants: {grade_info}")
            
        return pricing_data
        
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
            url = "https://www.cardmarket.com/en/Pokemon/Products/Singles/{}/{}".format(set_name, name)
            return {'prices': {}}, url
        
        # Convert EUR to USD using the configured rate
        if 'trendPrice' in prices:
            eur_price = prices['trendPrice']
            prices['trendPrice_usd'] = eur_price * EUR_TO_USD_CONVERSION_RATE
            prices['exchangeRate'] = EUR_TO_USD_CONVERSION_RATE  # Store the exchange rate used
            logger.debug("CardMarket price: €{} (${})".format(eur_price, prices['trendPrice_usd']))
        
        # Also convert avg1 if available
        if 'avg1' in prices:
            prices['avg1_usd'] = prices['avg1'] * EUR_TO_USD_CONVERSION_RATE
        
        return {'prices': prices}, url
    except Exception as e:
        logger.error("Error processing CardMarket prices: {}".format(str(e)))
        return {'prices': {}}, ''

# Add a utility function for handling API responses
def handle_api_response(response, default_value=None):
    """Safely handle API responses with better error handling"""
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        if response.status_code == 429:
            logger.warning(f"Rate limit exceeded: {err}")
            raise Exception("API rate limit exceeded. Please try again later.")
        else:
            logger.error(f"HTTP error: {err}")
            raise
    except requests.exceptions.RequestException as err:
        logger.error(f"Request error: {err}")
        raise
    except ValueError:
        logger.error("Invalid JSON response")
        if default_value is not None:
            return default_value
        raise Exception("Invalid response from API")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify({'suggestions': []})
    
    cache_key = f'search_{query.replace(" ", "_").lower()}'
    cached_data = get_cached_data(cache_key, max_age_hours=72)
    
    if cached_data:
        logger.info(f"Returning cached search results for '{query}'")
        return jsonify(cached_data)
    
    logger.info(f"Searching for cards matching '{query}'...")
    try:
        # Search with Pokemon TCG API
        response = requests.get(
            'https://api.pokemontcg.io/v2/cards',
            params={'q': f'name:*{query}*', 'orderBy': 'name', 'pageSize': 15},
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
        
        logger.info(f"Found {len(suggestions)} cards matching '{query}'")
        
        result = {'suggestions': suggestions}
        save_to_cache(cache_key, result)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error searching for '{query}': {str(e)}")
        return jsonify({'error': str(e), 'suggestions': []}), 500

@app.route('/api/card_prices')
def get_card_prices():
    card_id = request.args.get('id', '')
    
    if not card_id:
        return jsonify({'error': 'Card ID is required'}), 400
    
    cache_key = 'card_{}'.format(card_id)
    cached_data = get_cached_data(cache_key, max_age_hours=12)
    
    if cached_data:
        logger.info("Returning cached price data for card ID: {}".format(card_id))
        return jsonify(cached_data)
    
    logger.info("Fetching price data for card ID: {}".format(card_id))
    try:
        # Get card data from Pokemon TCG API using our client
        logger.info("Getting card details from Pokemon TCG API...")
        card_data = pokemon_tcg.get_card(card_id)
        
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
        
        logger.info("Processing card: {} from {}".format(card['name'], card['set']))
        
        # Get TCGPlayer prices (with detailed variants)
        logger.info("Extracting TCGPlayer pricing data...")
        tcgplayer_prices, tcgplayer_url = extract_tcgplayer_pricing(card_data)
        
        # Get PriceCharting prices with grading info - now passing the full card data
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
            'price_charting': pc_result.get('prices', {}),
            'pricecharting_url': pc_result.get('url', ''),
            'cardmarket': cm_result.get('prices', {}),
            'cardmarket_url': cm_url
        }
        
        # Calculate arbitrage opportunities
        logger.info("Calculating arbitrage opportunities...")
        result['arbitrage'] = calculate_arbitrage(result)
        
        if result['arbitrage']:
            logger.info("Found arbitrage opportunity! Buy: ${:.2f} Sell: ${:.2f} Profit: ${:.2f} ({:.2f}%)".format(
                result['arbitrage']['buy_price'], 
                result['arbitrage']['sell_price'], 
                result['arbitrage']['profit'], 
                result['arbitrage']['profit_margin']
            ))
        else:
            logger.info("No profitable arbitrage opportunities found")
        
        # Save to cache
        save_to_cache(cache_key, result)
        
        return jsonify(result)
    except Exception as e:
        logger.error("Error getting card prices: {}".format(str(e)))
        return jsonify({'error': str(e)}), 500

@app.route('/api/set_prices')
def get_set_prices():
    set_id = request.args.get('id', '')
    
    if not set_id:
        return jsonify({'error': 'Set ID is required'}), 400
    
    cache_key = f'set_{set_id}'
    cached_data = get_cached_data(cache_key, max_age_hours=12)
    
    if cached_data:
        logger.info(f"Returning cached set data for set ID: {set_id}")
        return jsonify(cached_data)
    
    logger.info(f"Analyzing set with ID: {set_id}")
    try:
        # Get set info - now using the client
        logger.info("Getting set information...")
        set_data = pokemon_tcg.get_set(set_id)
        
        set_name = set_data['name']
        logger.info(f"Analyzing set: {set_name}")
        
        # Get all cards in the set
        logger.info(f"Fetching cards from set '{set_name}'...")
        cards_data = pokemon_tcg.get_cards_in_set(set_id)
        
        result = {
            'set_id': set_id,
            'set_name': set_name,
            'set_series': set_data['series'],
            'cards': [],
            'exchange_rate': EUR_TO_USD_CONVERSION_RATE  # Add exchange rate to the result
        }
        
        # Process each card
        total_cards = len(cards_data)
        cards_with_prices = 0
        cards_with_arbitrage = 0
        
        logger.info(f"Processing {total_cards} cards in set '{set_name}'...")
        
        for i, card_data in enumerate(cards_data):
            if i % 10 == 0:
                logger.info(f"Processing cards: {i+1}/{total_cards}")
                
            card = {
                'id': card_data['id'],
                'name': card_data['name'],
                'number': card_data.get('number', ''),
                'rarity': card_data.get('rarity', ''),
                'image': card_data.get('images', {}).get('small', '')
            }
            
            # Skip energy cards and non-rare cards
            rarity = card_data.get('rarity', '').lower()
            if 'energy' in rarity or rarity in ['common', 'uncommon']:
                continue
            
            # Get prices from different sources
            try:
                # Extract TCGPlayer prices
                tcgplayer_prices, tcgplayer_url = extract_tcgplayer_pricing(card_data)
                card['tcgplayer'] = tcgplayer_prices
                card['tcgplayer_url'] = tcgplayer_url
                
                # Extract CardMarket prices
                cm_result, cm_url = get_cardmarket_prices(card_data)
                card['cardmarket'] = cm_result.get('prices', {})
                card['cardmarket_url'] = cm_url
                
                # Ensure CardMarket prices include both EUR and USD
                if 'cardmarket' in card and 'trendPrice' in card['cardmarket']:
                    # Add exchange rate for frontend use
                    card['cardmarket']['exchangeRate'] = EUR_TO_USD_CONVERSION_RATE
                    
                    # Ensure USD prices are calculated
                    if 'trendPrice_usd' not in card['cardmarket']:
                        card['cardmarket']['trendPrice_usd'] = card['cardmarket']['trendPrice'] * EUR_TO_USD_CONVERSION_RATE
                    
                    # Also convert avg1 if available
                    if 'avg1' in card['cardmarket'] and 'avg1_usd' not in card['cardmarket']:
                        card['cardmarket']['avg1_usd'] = card['cardmarket']['avg1'] * EUR_TO_USD_CONVERSION_RATE
                
                # Get PriceCharting prices - pass the full card data for better matching
                if tcgplayer_prices and 'market' in tcgplayer_prices and tcgplayer_prices['market'] > 5:
                    pc_result = get_pricecharting_prices(card_data)
                    card['price_charting'] = pc_result.get('prices', {})
                
                # Calculate arbitrage
                card['arbitrage'] = calculate_arbitrage(card)
                
                # Only include cards with price data
                has_prices = (
                    (tcgplayer_prices and 'market' in tcgplayer_prices) or
                    ('cardmarket' in card and 'trendPrice' in card['cardmarket'])
                )
                
                if has_prices:
                    result['cards'].append(card)
                    cards_with_prices += 1
                            
                    if card['arbitrage']:
                        cards_with_arbitrage += 1
                        
            except Exception as e:
                logger.error(f"Error processing card {card['name']}: {str(e)}")
        
        logger.info(f"Set analysis complete: {cards_with_prices} cards with pricing data, {cards_with_arbitrage} with arbitrage opportunities")
        # Sort by profitability
        result['cards'].sort(
            key=lambda x: x.get('arbitrage', {}).get('profit_margin', 0) if x.get('arbitrage') else 0,
            reverse=True
        )
        
        # Save to cache
        save_to_cache(cache_key, result)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing set: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sets')
def get_sets():
    cache_key = 'pokemon_sets'
    cached_data = get_cached_data(cache_key, max_age_hours=168)  # Cache for a week
    
    if cached_data:
        logger.info("Returning cached set list")
        return jsonify(cached_data)
    
    logger.info("Fetching all Pokemon card sets...")
    try:
        # Use Pokemon TCG API to get all sets
        response = requests.get('https://api.pokemontcg.io/v2/sets', 
                               headers={'X-Api-Key': POKE_API_KEY})
        
        # Check for rate limiting
        if response.status_code == 429:
            logger.warning("Rate limit hit for Pokemon TCG API")
            # Try to use cached data even if it's older
            older_cache = get_cached_data(cache_key, max_age_hours=720)  # 30 days
            if older_cache:
                logger.info("Using older cached data due to rate limit")
                return jsonify(older_cache)
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
        
        logger.info("Found {} Pokemon card sets".format(len(sets)))
        
        result = {'sets': sets}
        save_to_cache(cache_key, result)
        
        return jsonify(result)
    except Exception as e:
        logger.error("Error fetching sets: {}".format(str(e)))
        return jsonify({'error': str(e)}), 500    

def clear_cache():
    """Clear expired cache files"""
    logger.info("Clearing expired cache files...")
    count = 0
    for filename in os.listdir(cache_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(cache_dir, filename)
            file_age_hours = (time.time() - os.path.getmtime(filepath)) / 3600
            
            # Clear search cache after 3 days, card cache after 1 day
            max_age = 72 if 'search_' in filename else 24
            
            if file_age_hours > max_age:
                try:
                    os.remove(filepath)
                    count += 1
                except Exception as e:
                    logger.error(f"Error removing cache file {filepath}: {str(e)}")
                    
    logger.info(f"Cleared {count} expired cache files")

if __name__ == '__main__':
    # Clear expired cache on startup
    Thread(target=clear_cache).start()
    
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
    
    # Print cache status
    cache_count = len([f for f in os.listdir(cache_dir) if f.endswith('.json')])
    print("📦 Cache contains {} files".format(cache_count))
    
    print("\n📊 Starting web interface...")
    print("🌐 Access the tool in your browser at: http://127.0.0.1:5000")
    print("\n📊 Session Log:")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
