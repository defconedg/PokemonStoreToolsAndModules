"""API routes for the Pokemon Card Arbitrage Tool."""

from flask import Blueprint, jsonify, request, current_app
import logging
import json
from pokemon_arbitrage.core import calculate_arbitrage_opportunities
from pokemon_arbitrage.core.price_extractor import extract_all_prices

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

@api_bp.route('/card_prices', methods=['POST'])
def get_card_prices():
    """Get price data and arbitrage opportunities for a card."""
    try:
        card_data = request.json
        
        if not card_data:
            return jsonify({'error': 'No card data provided'}), 400
        
        # Extract all price points to include in response
        all_prices = extract_all_prices(card_data)
        
        # Check if PriceCharting data is valid
        if 'price_charting' in card_data:
            pc_data = card_data['price_charting']
            if isinstance(pc_data, dict) and 'status' in pc_data and pc_data['status'] == 'error':
                logger.warning(f"PriceCharting API error: {pc_data.get('error', 'Unknown error')}")
                # We'll continue without PriceCharting data
        
        # Get all arbitrage opportunities for this card
        arbitrage_opportunities = calculate_arbitrage_opportunities(card_data)
        
        # Extract variant information to help with UI display
        detected_variants = set()
        for price in all_prices:
            if price['variant']:
                detected_variants.add(price['variant'])
        
        # Return both the opportunities and a summary
        response = {
            'success': True,
            'card_name': card_data.get('name', 'Unknown Card'),
            'set_name': card_data.get('set', {}).get('name', 'Unknown Set'),
            'opportunities_count': len(arbitrage_opportunities),
            'opportunities': arbitrage_opportunities,
            'has_arbitrage': len(arbitrage_opportunities) > 0,
            'price_points': all_prices,
            'variants': list(detected_variants),
            'variant_count': len(detected_variants)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.exception(f"Error processing card prices: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process card prices',
            'error_detail': str(e)
        }), 500
