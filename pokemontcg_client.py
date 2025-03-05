import os
import requests
import logging
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class PokemonTCGClient:
    """
    Main client for interacting with the Pokemon TCG API (pokemontcg.io)
    """
    BASE_URL = "https://api.pokemontcg.io/v2"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the client with optional API key
        """
        # Use API key from param, environment variable, or None
        self.api_key = api_key or os.environ.get('POKEMONTCG_IO_API_KEY')
        self.headers = {'X-Api-Key': self.api_key} if self.api_key else {}
    
    def get_card(self, card_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific card
        """
        try:
            response = requests.get(f"{self.BASE_URL}/cards/{card_id}", headers=self.headers)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logger.error(f"Error getting card {card_id}: {str(e)}")
            raise
    
    def search_cards(self, query: str, page: int = 1, page_size: int = 15) -> Dict[str, Any]:
        """
        Search for cards based on query
        """
        try:
            params = {
                'q': query,
                'page': page,
                'pageSize': page_size,
                'orderBy': 'name'
            }
            response = requests.get(f"{self.BASE_URL}/cards", params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching cards with query '{query}': {str(e)}")
            raise
    
    def get_set(self, set_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific set
        """
        try:
            response = requests.get(f"{self.BASE_URL}/sets/{set_id}", headers=self.headers)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logger.error(f"Error getting set {set_id}: {str(e)}")
            raise
    
    def get_sets(self) -> List[Dict[str, Any]]:
        """
        Get list of all available sets
        """
        try:
            response = requests.get(f"{self.BASE_URL}/sets", headers=self.headers)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logger.error(f"Error getting sets: {str(e)}")
            raise
    
    def get_cards_in_set(self, set_id: str, page_size: int = 250) -> List[Dict[str, Any]]:
        """
        Get all cards in a specific set
        """
        try:
            params = {
                'q': f'set.id:{set_id}',
                'pageSize': page_size
            }
            response = requests.get(f"{self.BASE_URL}/cards", params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logger.error(f"Error getting cards in set {set_id}: {str(e)}")
            raise
            
    def extract_card_variants(self, card_data: Dict[str, Any]) -> tuple:
        """
        Extract and normalize pricing variants from TCGPlayer data
        
        Args:
            card_data: Card data from Pokemon TCG API
            
        Returns:
            tuple: (prices_dict, tcgplayer_url)
        """
        try:
            tcgplayer = card_data.get('tcgplayer', {})
            prices = {}
            url = tcgplayer.get('url', '')
            
            if not tcgplayer or not tcgplayer.get('prices'):
                # Build a fallback URL if none exists
                set_name = card_data.get('set', {}).get('name', '').replace(' ', '-').lower()
                card_name = card_data.get('name', '').replace(' ', '-').lower()
                url = f"https://www.tcgplayer.com/search/pokemon/{set_name}?q={card_name}"
                return {}, url
                
            # Extract pricing variants
            tcg_prices = tcgplayer.get('prices', {})
            
            # Store condition information to help with arbitrage
            prices['condition_info'] = {
                'source': 'TCGPlayer',
                'preferred_condition': 'Near Mint',
                'available_conditions': []
            }
            
            # Identify the primary variant (normal, holofoil, reverse holofoil, etc.)
            primary_variant = None
            has_holofoil = 'holofoil' in tcg_prices
            has_reverse_holo = 'reverseHolofoil' in tcg_prices
            has_normal = 'normal' in tcg_prices
            has_1st_edition = '1stEditionHolofoil' in tcg_prices
            
            if has_holofoil:
                primary_variant = 'holofoil'
                prices['is_holofoil'] = True
            elif has_reverse_holo:
                primary_variant = 'reverseHolofoil'
                prices['is_reverse_holo'] = True
            elif has_normal:
                primary_variant = 'normal'
            elif has_1st_edition:
                primary_variant = '1stEditionHolofoil'
                prices['is_first_edition'] = True
            
            # Add info about which variants are available
            prices['primary_variant'] = primary_variant
            prices['available_variants'] = list(tcg_prices.keys())
            
            # Process each variant's pricing data
            for variant, variant_prices in tcg_prices.items():
                # For each variant, we store its complete price data
                prices[variant] = variant_prices
                prices['condition_info']['available_conditions'].append(variant)
                
                # If this is the primary variant, extract its pricing for top-level access
                if primary_variant and variant == primary_variant:
                    # Always prioritize Near Mint pricing (high price) for arbitrage
                    # Market price is an average of recent sales across conditions
                    if 'high' in variant_prices:
                        prices['near_mint'] = variant_prices['high']
                        
                    # Add other metrics, but flag the primary one for arbitrage
                    for price_type in ['market', 'low', 'mid', 'high']:
                        if price_type in variant_prices:
                            prices[price_type] = variant_prices[price_type]
            
            # If near_mint price isn't available (no high price), use market as fallback
            if 'market' in prices and 'near_mint' not in prices:
                prices['near_mint'] = prices['market']
                prices['condition_info']['note'] = 'Using market price as Near Mint substitute'
            
            # Flag if we have reliable Near Mint pricing
            prices['has_near_mint_price'] = 'near_mint' in prices
            
            return prices, url
        
        except Exception as e:
            logging.error(f"Error extracting TCGPlayer variants: {str(e)}")
            return {}, ""
