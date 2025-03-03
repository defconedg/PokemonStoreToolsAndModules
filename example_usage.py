"""
Example usage of the PriceCharting API wrapper and Pokemon TCG API
"""

import json
from price_charting import PriceCharting
from pokemontcg_client import PokemonTCGClient
from config import PRICE_CHARTING_API_TOKEN, POKEMON_TCG_API_KEY, SET_MAPPINGS

def main():
    # Initialize the client using the token from config.py
    price_charting = PriceCharting(PRICE_CHARTING_API_TOKEN)
    
    # Example 1: Get product by ID (EarthBound)
    print("\n--- Example 1: Product Lookup by ID ---")
    product = price_charting.get_product_by_id("6910")  # EarthBound
    print(f"Product Name: {product['product-name']}")
    print(f"Console: {product['console-name']}")
    print(f"Loose Price: ${price_charting.cents_to_dollars(product.get('loose-price', 0)):.2f}")
    print(f"CIB Price: ${price_charting.cents_to_dollars(product.get('cib-price', 0)):.2f}")
    
    # Example 2: Search for products
    print("\n--- Example 2: Product Search ---")
    results = price_charting.search_products("Pokémon Red")
    print(f"Found {len(results.get('products', []))} products:")
    for product in results.get('products', [])[:3]:  # Show first 3 results
        print(f"- {product['product-name']} ({product['console-name']}): ID {product['id']}")
    
    # Example 3: Get complete product details with all price points
    print("\n--- Example 3: Complete Product Details ---")
    details = price_charting.get_complete_product_details("6910")
    print(f"Product: {details['product_name']} ({details['console_name']})")
    print(f"Loose Price: ${details['prices']['loose']:.2f}")
    print(f"CIB Price: ${details['prices']['cib']:.2f}")
    print(f"New Price: ${details['prices']['new']:.2f}")
    if 'graded' in details['prices']:
        print(f"Graded Price: ${details['prices']['graded']:.2f}")
    if 'box_only' in details['prices']:
        print(f"Box Only Price: ${details['prices']['box_only']:.2f}")
    if 'manual_only' in details['prices']:
        print(f"Manual Only Price: ${details['prices']['manual_only']:.2f}")
    
    # Example 4: Search by console
    print("\n--- Example 4: Console-specific Search ---")
    nintendo_64_games = price_charting.search_by_console("nintendo 64", "mario")
    print("Mario games for Nintendo 64:")
    for game in nintendo_64_games.get('products', [])[:5]:  # Show first 5 results
        print(f"- {game['product-name']}")
    
    # Example 5: Get product by UPC
    print("\n--- Example 5: Product Lookup by UPC ---")
    try:
        product = price_charting.get_product_by_upc("045496830434")  # Example UPC
        print(f"Product Name: {product['product-name']}")
        print(f"Console: {product['console-name']}")
        print(f"Loose Price: ${price_charting.cents_to_dollars(product.get('loose-price', 0)):.2f}")
    except Exception as e:
        print(f"Error looking up product by UPC: {str(e)}")
    
    # Example 6: Get product by name (returns best match)
    print("\n--- Example 6: Product Lookup by Name ---")
    product = price_charting.get_product_by_name("Legend of Zelda Ocarina of Time")
    print(f"Product Name: {product['product-name']}")
    print(f"Console: {product['console-name']}")
    print(f"ID: {product['id']}")

    # Example 7: Get complete data for a specific Pokémon card
    print("\n--- Example 7: Pokémon Card Data (Squirtle 170/165 from SV 151) ---")
    # First search for the card with more specific terms to get the English version
    search_results = price_charting.search_products("Squirtle 170/165 English 151 MEW Pokemon Card")
    
    if search_results.get("status") == "success" and search_results.get("products"):
        # Display search results
        print("Search Results:")
        for i, card in enumerate(search_results.get("products", [])[:5]):
            print(f"{i+1}. {card['product-name']} ({card['console-name']}): ID {card['id']}")
        
        # Get the first result's ID (assuming it's the correct card)
        if search_results.get("products"):
            card_id = search_results["products"][0]["id"]
            
            # Get complete details for the card
            card_details = price_charting.get_complete_product_details(card_id)
            
            print("\nCard Details:")
            print(f"Name: {card_details['product_name']}")
            print(f"Set: {card_details.get('console_name', '')}")
            
            # Display release date if available
            if card_details.get("release_date"):
                print(f"Release Date: {card_details['release_date']}")
            
            print("\nPricing Information:")
            # Display all pricing information available for the card
            prices = card_details["prices"]
            
            # Standard prices for Pokemon cards
            print(f"Ungraded Price: ${prices.get('loose', 0):.2f}")
            
            # Graded prices - display if available
            graded_prices = {
                "PSA 7": prices.get('cib', 0),
                "PSA 8": prices.get('new', 0),
                "PSA 9": prices.get('graded', 0),
                "PSA 10": prices.get('manual_only', 0),  # Manual_only for cards is PSA 10
                "BGS 9.5": prices.get('box_only', 0),    # Box_only for cards is BGS 9.5
                "BGS 10": prices.get('bgs_10', 0),
                "CGC 10": prices.get('cgc_10', 0),
                "SGC 10": prices.get('sgc_10', 0)
            }
            
            for grade, price in graded_prices.items():
                if price > 0:
                    print(f"{grade} Price: ${price:.2f}")
            
            # Retail pricing if available
            retail_prices = {
                "Retail Buy (Loose)": prices.get('retail_loose_buy', 0),
                "Retail Sell (Loose)": prices.get('retail_loose_sell', 0)
            }
            
            for label, price in retail_prices.items():
                if price > 0:
                    print(f"{label}: ${price:.2f}")
    else:
        print("Could not find the specified Pokémon card. Check the search terms.")
        
    # Example 8: Get the same Squirtle card data from Pokemon TCG API (simplified)
    print("\n--- Example 8: Pokemon TCG API - Squirtle 170/165 from SV 151 ---")
    
    # Initialize the Pokemon TCG client
    pokemon_tcg = PokemonTCGClient(POKEMON_TCG_API_KEY)
    
    # Define the set we're looking for
    target_set = "Pokemon 151"
    
    # Find the set ID from our mappings
    set_id = None
    for set_name, set_info in SET_MAPPINGS.items():
        # Try different matching strategies
        if (set_name.lower() == target_set.lower() or 
            "151" in set_name or 
            set_name.lower() in target_set.lower() or 
            target_set.lower() in set_name.lower()):
            set_id = set_info["tcg_id"]
            print(f"Found set ID {set_id} for {set_name} in our mappings")
            break
    
    # If not found in mappings, search the API directly
    if not set_id:
        # Try multiple search terms for better results
        search_terms = [
            'name:"Pokemon 151"', 
            'name:151', 
            'name:"151"',
            'name:sv3pt5'
        ]
        
        for search_term in search_terms:
            print(f"Searching for set with query: {search_term}")
            sets_response = pokemon_tcg.sets.search(query=search_term)
            
            if sets_response.get('data'):
                set_id = sets_response['data'][0]['id']
                print(f"Found set with ID: {set_id}")
                break
    
    if not set_id:
        print("Could not find the Pokemon 151 set. Listing available sets:")
        all_sets = pokemon_tcg.sets.all()
        for s in all_sets[:10]:  # Show first 10 sets
            print(f"- {s['name']} (ID: {s['id']})")
        print("\nExamples completed successfully!")
        return
    
    # Now search directly for the Squirtle card by its number in the set
    card_id = f"{set_id}-170"  # Format: set_id-card_number
    print(f"Looking for card with ID: {card_id}")
    
    try:
        # Try direct lookup by ID first
        card = pokemon_tcg.cards.find(card_id)
        print(f"Found card by direct ID lookup: {card['name']}")
    except Exception as e:
        print(f"Direct lookup failed: {str(e)}")
        print("Falling back to search...")
        
        # Fall back to search if direct lookup fails
        search_query = f'number:170 set.id:{set_id}'
        card_results = pokemon_tcg.cards.search(query=search_query)
        
        if not card_results.get('data'):
            # Try broader search
            search_query = f'name:squirtle set.id:{set_id}'
            print(f"Trying broader search: {search_query}")
            card_results = pokemon_tcg.cards.search(query=search_query)
            
            if not card_results.get('data'):
                print(f"No Squirtle cards found in set {set_id}. Showing available cards:")
                # Show some cards from the set to verify we have the right set
                set_cards = pokemon_tcg.cards.search(query=f'set.id:{set_id}')
                if set_cards.get('data'):
                    for c in set_cards['data'][:5]:
                        print(f"- {c['name']} (Number: {c['number']})")
                print("\nExamples completed successfully!")
                return
        
        card = card_results['data'][0]
    
    # Display card details
    print(f"\nCard Found: {card['name']} ({card['number']}/{card['set']['printedTotal']})")
    print(f"Set: {card['set']['name']} ({card['set']['id']})")
    print(f"Rarity: {card['rarity']}")
    print(f"Artist: {card['artist']}")
    
    # Display card images
    print("\nCard Images:")
    print(f"Small: {card['images'].get('small', 'N/A')}")
    print(f"Large: {card['images'].get('large', 'N/A')}")
    
    # Display pricing information if available
    if card.get('tcgplayer') and card['tcgplayer'].get('prices'):
        print("\nTCGPlayer Pricing:")
        prices = card['tcgplayer']['prices']
        
        for variant, price_data in prices.items():
            print(f"{variant.title()}:")
            print(f"  Market Price: ${price_data.get('market', 'N/A')}")
            print(f"  Low: ${price_data.get('low', 'N/A')}")
            print(f"  Mid: ${price_data.get('mid', 'N/A')}")
            print(f"  High: ${price_data.get('high', 'N/A')}")

    print("\nExamples completed successfully!")

if __name__ == "__main__":
    main()
