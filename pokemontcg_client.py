import os
import requests
from typing import Dict, List, Any, Optional, Union

class PokemonTCGClient:
    """
    Main client for interacting with the Pokemon TCG API (pokemontcg.io)
    """
    BASE_URL = "https://api.pokemontcg.io/v2"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the client with optional API key
        
        Args:
            api_key: Your API key from the Pokemon TCG Developer Portal
        """
        # Use API key from param, environment variable, or None
        self.api_key = api_key or os.environ.get('POKEMONTCG_IO_API_KEY')
        self.headers = {'X-Api-Key': self.api_key} if self.api_key else {}
        
        # Initialize resource classes
        self.cards = Cards(self)
        self.sets = Sets(self)
        self.types = ResourceList(self, "types")
        self.subtypes = ResourceList(self, "subtypes")
        self.supertypes = ResourceList(self, "supertypes")
        self.rarities = ResourceList(self, "rarities")
    
    def request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make a request to the API
        
        Args:
            endpoint: API endpoint to request
            params: Query parameters
            
        Returns:
            JSON response data
        """
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        
        # Handle errors
        response.raise_for_status()
        return response.json()

class Cards:
    """Class for interacting with the cards endpoint"""
    
    def __init__(self, client: PokemonTCGClient):
        self.client = client
    
    def find(self, card_id: str, select: str = None) -> Dict:
        """
        Find a single card by ID
        
        Args:
            card_id: The card's unique identifier
            select: Optional comma-separated list of fields to return
            
        Returns:
            Card data
        """
        params = {}
        if select:
            params['select'] = select
        
        response = self.client.request(f"cards/{card_id}", params)
        return response['data']
    
    def search(self, query: str = None, page: int = 1, page_size: int = 250, 
               order_by: str = None, select: str = None) -> Dict:
        """
        Search for cards with a query
        
        Args:
            query: Search query using Lucene syntax (e.g., "name:charizard subtypes:mega")
            page: Page number for pagination
            page_size: Number of results per page (max 250)
            order_by: Field(s) to order results by
            select: Optional comma-separated list of fields to return
            
        Returns:
            Dict containing cards and pagination info
        """
        params = {
            'page': page,
            'pageSize': page_size
        }
        
        if query:
            params['q'] = query
        if order_by:
            params['orderBy'] = order_by
        if select:
            params['select'] = select
        
        return self.client.request("cards", params)
    
    def all(self) -> List[Dict]:
        """
        Get all cards (automatically handles pagination)
        WARNING: This may take a long time and use a lot of API calls
        
        Returns:
            List of all cards
        """
        all_cards = []
        page = 1
        has_more = True
        
        while has_more:
            response = self.search(page=page)
            all_cards.extend(response['data'])
            page += 1
            has_more = response['count'] == response['pageSize'] and response['count'] > 0
            
        return all_cards
    
    def where(self, q: str = None, page: int = 1, page_size: int = 250, 
              order_by: str = None, select: str = None) -> Dict:
        """
        Alias for search() to match the Python SDK syntax
        """
        return self.search(query=q, page=page, page_size=page_size, 
                           order_by=order_by, select=select)
    
    def get_prices(self, card_id: str) -> Dict:
        """
        Get pricing information for a card
        
        Args:
            card_id: The card's unique identifier
            
        Returns:
            Pricing information from TCGPlayer
        """
        card = self.find(card_id, select="tcgplayer")
        return card.get('tcgplayer', {}).get('prices', {})
    
    def get_image(self, card_id: str, size: str = "large") -> str:
        """
        Get a card's image URL
        
        Args:
            card_id: The card's unique identifier
            size: 'small' or 'large'
            
        Returns:
            URL to the card image
        """
        card = self.find(card_id, select="images")
        return card.get('images', {}).get(size, None)

class Sets:
    """Class for interacting with the sets endpoint"""
    
    def __init__(self, client: PokemonTCGClient):
        self.client = client
    
    def find(self, set_id: str, select: str = None) -> Dict:
        """
        Find a single set by ID
        
        Args:
            set_id: The set's unique identifier
            select: Optional comma-separated list of fields to return
            
        Returns:
            Set data
        """
        params = {}
        if select:
            params['select'] = select
            
        response = self.client.request(f"sets/{set_id}", params)
        return response['data']
    
    def search(self, query: str = None, page: int = 1, page_size: int = 250, 
               order_by: str = None, select: str = None) -> Dict:
        """
        Search for sets with a query
        
        Args:
            query: Search query using Lucene syntax (e.g., "series:base")
            page: Page number for pagination
            page_size: Number of results per page (max 250)
            order_by: Field(s) to order results by
            select: Optional comma-separated list of fields to return
            
        Returns:
            Dict containing sets and pagination info
        """
        params = {
            'page': page,
            'pageSize': page_size
        }
        
        if query:
            params['q'] = query
        if order_by:
            params['orderBy'] = order_by
        if select:
            params['select'] = select
        
        return self.client.request("sets", params)
    
    def all(self) -> List[Dict]:
        """
        Get all sets (handles pagination automatically)
        
        Returns:
            List of all sets
        """
        all_sets = []
        page = 1
        has_more = True
        
        while has_more:
            response = self.search(page=page)
            all_sets.extend(response['data'])
            page += 1
            has_more = response['count'] == response['pageSize'] and response['count'] > 0
            
        return all_sets
    
    def where(self, q: str = None, page: int = 1, page_size: int = 250, 
              order_by: str = None, select: str = None) -> Dict:
        """
        Alias for search() to match the Python SDK syntax
        """
        return self.search(query=q, page=page, page_size=page_size, 
                           order_by=order_by, select=select)
    
    def get_images(self, set_id: str) -> Dict[str, str]:
        """
        Get a set's images (symbol and logo)
        
        Args:
            set_id: The set's unique identifier
            
        Returns:
            Dict with symbol and logo URLs
        """
        set_data = self.find(set_id, select="images")
        return set_data.get('images', {})

class ResourceList:
    """Generic class for simple resource list endpoints"""
    
    def __init__(self, client: PokemonTCGClient, resource_type: str):
        self.client = client
        self.resource_type = resource_type
    
    def all(self) -> List[str]:
        """
        Get all resources of this type
        
        Returns:
            List of all resources
        """
        response = self.client.request(self.resource_type)
        return response['data']

# Utility functions

def configure_api_key(api_key: str) -> None:
    """
    Configure the API key globally for all future client instances
    
    Args:
        api_key: Your API key from the Pokemon TCG Developer Portal
    """
    os.environ['POKEMONTCG_IO_API_KEY'] = api_key

# Example usage functions

def get_card_details(card_id: str) -> Dict:
    """
    Get detailed information about a card
    
    Args:
        card_id: Card ID (e.g., 'swsh1-1')
        
    Returns:
        Card details
    """
    client = PokemonTCGClient()
    return client.cards.find(card_id)

def search_cards(query: str, page: int = 1) -> List[Dict]:
    """
    Search for cards with a simple query
    
    Args:
        query: Search query (e.g., 'name:charizard')
        page: Page number
        
    Returns:
        List of matching cards
    """
    client = PokemonTCGClient()
    response = client.cards.search(query=query, page=page)
    return response['data']

def get_card_image(card_id: str, large: bool = True) -> str:
    """
    Get a card's image URL
    
    Args:
        card_id: Card ID (e.g., 'swsh1-1')
        large: Whether to get the large image (True) or small image (False)
        
    Returns:
        Image URL as a string
    """
    client = PokemonTCGClient()
    size = "large" if large else "small"
    return client.cards.get_image(card_id, size)

def get_card_prices(card_id: str) -> Dict:
    """
    Get the current market prices for a card
    
    Args:
        card_id: Card ID (e.g., 'swsh1-1')
        
    Returns:
        Dict with pricing information
    """
    client = PokemonTCGClient()
    return client.cards.get_prices(card_id)

def get_set_details(set_id: str) -> Dict:
    """
    Get detailed information about a set
    
    Args:
        set_id: Set ID (e.g., 'swsh1')
        
    Returns:
        Set details
    """
    client = PokemonTCGClient()
    return client.sets.find(set_id)

def get_set_images(set_id: str) -> Dict:
    """
    Get the symbol and logo images for a set
    
    Args:
        set_id: Set ID (e.g., 'swsh1')
        
    Returns:
        Dict with symbol and logo URLs
    """
    client = PokemonTCGClient()
    return client.sets.get_images(set_id)

def get_all_types() -> List[str]:
    """
    Get all Pokémon card types
    
    Returns:
        List of types (e.g., ['Fire', 'Water', ...])
    """
    client = PokemonTCGClient()
    return client.types.all()

def get_all_rarities() -> List[str]:
    """
    Get all card rarities
    
    Returns:
        List of rarities (e.g., ['Common', 'Rare', ...])
    """
    client = PokemonTCGClient()
    return client.rarities.all()

# Example of advanced filtering
def find_cards_with_advanced_query(query: str) -> List[Dict]:
    """
    Find cards using advanced query syntax
    
    Args:
        query: Advanced query (see pokemontcg.io docs for syntax)
        
    Returns:
        List of matching cards
    """
    client = PokemonTCGClient()
    response = client.cards.search(query=query)
    return response['data']
