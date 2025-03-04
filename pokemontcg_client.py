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
        Extract and normalize pricing variants for a card
        """
        if 'tcgplayer' not in card_data:
            return None, None
            
        tcgplayer = card_data.get('tcgplayer', {})
        prices = tcgplayer.get('prices', {})
        url = tcgplayer.get('url', '')
        
        # Create standardized structure
        result = {}
        
        # All possible price variants based on Pokemon TCG API documentation
        price_variants = [
            'normal', 'holofoil', '1stEditionHolofoil', '1stEditionNormal',
            'unlimited', 'unlimitedHolofoil', 'reverseHolofoil'
        ]
        
        # Find prices for all variants
        for variant in price_variants:
            if variant in prices:
                variant_data = prices[variant]
                # Store the variant's prices
                result[variant] = variant_data
                
                # Set main market price if not already set
                if 'market' not in result and 'market' in variant_data:
                    result['market'] = variant_data['market']
                    result['primary_variant'] = variant
                    
        # Additional metadata about the card's printing
        result['is_holofoil'] = any('holo' in v.lower() for v in prices.keys())
        result['is_first_edition'] = any('1st' in v for v in prices.keys())
        result['is_reverse_holo'] = 'reverseHolofoil' in prices
        
        return result, url
