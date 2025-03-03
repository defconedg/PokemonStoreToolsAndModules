"""
Pokemon Price Helper
Combines functionality from PokemonTCG API and PriceCharting API
for easy price comparisons and data retrieval
"""

import os
from typing import Dict, List, Any, Optional, Union, Tuple
from pokemontcg_client import PokemonTCGClient
from price_charting import PriceCharting

class PokemonPriceHelper:
    """
    Helper class that combines PokemonTCG API and PriceCharting API
    to provide easy access to Pokemon card pricing and information
    """
    
    def __init__(self, tcg_api_key: str = None, pricecharting_api_key: str = None):
        """
        Initialize with API keys for both services
        
        Args:
            tcg_api_key: API key for PokemonTCG.io
            pricecharting_api_key: API key for PriceCharting
        """
        # Get API keys from params or environment variables
        self.tcg_api_key = tcg_api_key or os.environ.get('POKEMONTCG_IO_API_KEY')
        self.pricecharting_api_key = pricecharting_api_key or os.environ.get('PRICECHARTING_API_KEY')
        
        # Initialize API clients
        self.tcg = PokemonTCGClient(self.tcg_api_key) if self.tcg_api_key else None
        self.price_charting = PriceCharting(self.pricecharting_api_key) if self.pricecharting_api_key else None
        
    def get_card_by_name(self, name: str) -> Dict:
        """
        Find a Pokemon card by name using PokemonTCG API
        
        Args:
            name: Card name (e.g., 'Charizard')
            
        Returns:
            Best matching card data
        """
        if not self.tcg:
            raise ValueError("PokemonTCG API key not provided")
            
        response = self.tcg.cards.search(query=f"name:{name}")
        if response.get('data') and len(response['data']) > 0:
            return response['data'][0]
        return {"status": "error", "message": f"No card found with name: {name}"}
        
    def get_card_by_id(self, card_id: str) -> Dict:
        """
        Get Pokemon card details by ID
        
        Args:
            card_id: Card ID (e.g., 'swsh4-19')
            
        Returns:
            Card data
        """
        if not self.tcg:
            raise ValueError("PokemonTCG API key not provided")
            
        return self.tcg.cards.find(card_id)
        
    def get_card_price_data(self, card_id: str) -> Dict:
        """
        Get pricing data for a Pokemon card from PokemonTCG API
        
        Args:
            card_id: Card ID (e.g., 'swsh4-19')
            
        Returns:
            Card pricing data from TCGPlayer
        """
        if not self.tcg:
            raise ValueError("PokemonTCG API key not provided")
            
        card = self.tcg.cards.find(card_id, select="tcgplayer")
        return card.get('tcgplayer', {}).get('prices', {})
    
    def get_price_charting_data(self, query: str) -> Dict:
        """
        Get pricing data from PriceCharting
        
        Args:
            query: Search query (e.g., 'Pokemon Red')
            
        Returns:
            Price data
        """
        if not self.price_charting:
            raise ValueError("PriceCharting API key not provided")
            
        product = self.price_charting.get_product_by_name(query)
        if product['status'] != 'success':
            return {"status": "error", "message": f"No product found for: {query}"}
            
        return self.price_charting.get_complete_product_details(product['id'])
        
    def compare_prices(self, card_name: str) -> Dict:
        """
        Compare prices between PokemonTCG and PriceCharting data
        
        Args:
            card_name: Name of the card/game (e.g., 'Charizard' or 'Pokemon Red')
            
        Returns:
            Comparative price data from both sources
        """
        result = {"card_name": card_name, "sources": {}}
        
        # Get PokemonTCG data if available
        if self.tcg:
            try:
                tcg_card = self.get_card_by_name(card_name)
                if tcg_card.get('id'):
                    tcg_prices = self.get_card_price_data(tcg_card['id'])
                    result["sources"]["pokemontcg"] = {
                        "name": tcg_card.get('name', 'Unknown'),
                        "set": tcg_card.get('set', {}).get('name', 'Unknown'),
                        "prices": tcg_prices,
                        "image": tcg_card.get('images', {}).get('large')
                    }
            except Exception as e:
                result["sources"]["pokemontcg"] = {
                    "error": str(e)
                }
        
        # Get PriceCharting data if available
        if self.price_charting:
            try:
                pc_data = self.get_price_charting_data(card_name)
                if pc_data.get('status') == 'success':
                    result["sources"]["pricecharting"] = {
                        "name": pc_data.get('product_name', 'Unknown'),
                        "console": pc_data.get('console_name', 'Unknown'),
                        "prices": pc_data.get('prices', {}),
                        "image_url": pc_data.get('image_url')
                    }
            except Exception as e:
                result["sources"]["pricecharting"] = {
                    "error": str(e)
                }
        
        return result
    
    def search_cards(self, query: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """
        Search for cards using PokemonTCG API
        
        Args:
            query: Search query
            page: Page number
            page_size: Number of results per page
            
        Returns:
            List of matching cards
        """
        if not self.tcg:
            raise ValueError("PokemonTCG API key not provided")
            
        response = self.tcg.cards.search(query=query, page=page, page_size=page_size)
        return response.get('data', [])
    
    def get_set_list(self) -> List[Dict]:
        """
        Get list of all Pokemon card sets
        
        Returns:
            List of sets
        """
        if not self.tcg:
            raise ValueError("PokemonTCG API key not provided")
            
        response = self.tcg.sets.search(order_by="releaseDate")
        return response.get('data', [])
    
    def get_console_games(self, console_name: str, search_term: str = "") -> List[Dict]:
        """
        Search for games on a specific console using PriceCharting
        
        Args:
            console_name: Name of the console (e.g., 'nintendo 64')
            search_term: Optional search term to filter results
            
        Returns:
            List of games
        """
        if not self.price_charting:
            raise ValueError("PriceCharting API key not provided")
            
        results = self.price_charting.search_by_console(console_name, search_term)
        return results.get('products', [])
    
    def get_card_images(self, card_id: str) -> Dict:
        """
        Get high and low resolution images for a card
        
        Args:
            card_id: Card ID
            
        Returns:
            Dict with image URLs
        """
        if not self.tcg:
            raise ValueError("PokemonTCG API key not provided")
            
        card = self.tcg.cards.find(card_id, select="images")
        return card.get('images', {})
    
    def track_collection_value(self, product_ids: List[str]) -> Dict:
        """
        Track the value of a collection of items from PriceCharting
        
        Args:
            product_ids: List of PriceCharting product IDs
            
        Returns:
            Collection value information
        """
        if not self.price_charting:
            raise ValueError("PriceCharting API key not provided")
            
        total_value = 0
        items = []
        
        for product_id in product_ids:
            try:
                details = self.price_charting.get_complete_product_details(product_id)
                if details["status"] == "success":
                    loose_value = details["prices"]["loose"] or 0
                    cib_value = details["prices"]["cib"] or 0
                    new_value = details["prices"]["new"] or 0
                    
                    # Use the highest available price
                    best_value = max(loose_value, cib_value, new_value)
                    total_value += best_value
                    
                    items.append({
                        "name": details["product_name"],
                        "console": details["console_name"],
                        "loose_value": loose_value,
                        "cib_value": cib_value, 
                        "new_value": new_value,
                        "best_value": best_value
                    })
            except Exception as e:
                items.append({
                    "product_id": product_id,
                    "error": str(e)
                })
        
        return {
            "items": items,
            "total_value": total_value,
            "count": len(items)
        }

# Example usage
def main():
    # Initialize with environment variables
    helper = PokemonPriceHelper()
    
    # Example 1: Get card by name
    card = helper.get_card_by_name("Charizard")
    print(f"Found card: {card.get('name')} from set {card.get('set', {}).get('name')}")
    
    # Example 2: Compare prices
    prices = helper.compare_prices("Pikachu")
    print(f"Price comparison for {prices['card_name']}:")
    if "pokemontcg" in prices["sources"]:
        print(f"  TCG API: {prices['sources']['pokemontcg'].get('name')}")
        print(f"    Set: {prices['sources']['pokemontcg'].get('set')}")
        print(f"    Prices: {prices['sources']['pokemontcg'].get('prices')}")
    
    if "pricecharting" in prices["sources"]:
        print(f"  PriceCharting: {prices['sources']['pricecharting'].get('name')}")
        print(f"    Console: {prices['sources']['pricecharting'].get('console')}")
        print(f"    Prices: {prices['sources']['pricecharting'].get('prices')}")
    
    # Example 3: Search for cards
    cards = helper.search_cards("type:fire rarity:rare")
    print(f"Found {len(cards)} fire type rare cards")
    
    # Example 4: Get console games
    games = helper.get_console_games("nintendo 64", "zelda")
    print(f"Found {len(games)} Zelda games for Nintendo 64")
    for game in games[:3]:  # Show first 3
        print(f"  {game.get('product-name')}")

if __name__ == "__main__":
    main()
