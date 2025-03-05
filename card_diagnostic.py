#!/usr/bin/env python
"""
Test script for Pokemon TCG API and PriceCharting API integration.
Tests various cards to identify issues with API calls and matching.

Usage:
    python pokemon_api_test.py
"""

import os
import sys
import json
import requests
from typing import Dict, Any, List, Optional, Tuple
import time

# API keys - use the provided values
POKEMON_API_KEY = "de7a1097-afd8-4511-b9fa-6a36c18c7759"
PRICECHARTING_API_KEY = "3ada03b1de794bed535db04c27d9141af942fbd7"

# Load set mappings
SET_MAPPING = {
    "base1": {"tcg_name": "Base", "pricecharting_name": "Pokemon Base Set"},
    "base2": {"tcg_name": "Jungle", "pricecharting_name": "Pokemon Jungle"},
    "basep": {"tcg_name": "Wizards Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "base3": {"tcg_name": "Fossil", "pricecharting_name": "Pokemon Fossil"},
    "base4": {"tcg_name": "Base Set 2", "pricecharting_name": "Pokemon Base Set 2"},
    "base5": {"tcg_name": "Team Rocket", "pricecharting_name": "Pokemon Team Rocket"},
    "gym1": {"tcg_name": "Gym Heroes", "pricecharting_name": "Pokemon Gym Heroes"},
    "gym2": {"tcg_name": "Gym Challenge", "pricecharting_name": "Pokemon Gym Challenge"},
    "neo1": {"tcg_name": "Neo Genesis", "pricecharting_name": "Pokemon Neo Genesis"},
    "neo4": {"tcg_name": "Neo Destiny", "pricecharting_name": "Pokemon Neo Destiny"},
    "base6": {"tcg_name": "Legendary Collection", "pricecharting_name": "Pokemon Legendary Treasures"},
    "ecard1": {"tcg_name": "Expedition Base Set", "pricecharting_name": "Pokemon Ancient Origins"},
    "np": {"tcg_name": "Nintendo Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "ex8": {"tcg_name": "Deoxys", "pricecharting_name": "Pokemon Deoxys"},
    "ex15": {"tcg_name": "Dragon Frontiers", "pricecharting_name": "Pokemon Dragon Frontiers"},
    "dpp": {"tcg_name": "DP Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "hsp": {"tcg_name": "HGSS Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "bwp": {"tcg_name": "BW Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "xyp": {"tcg_name": "XY Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "bw11": {"tcg_name": "Legendary Treasures", "pricecharting_name": "Pokemon Legendary Treasures"},
    "xy2": {"tcg_name": "Flashfire", "pricecharting_name": "Pokemon Flashfire"},
    "xy7": {"tcg_name": "Ancient Origins", "pricecharting_name": "Pokemon Ancient Origins"},
    "g1": {"tcg_name": "Generations", "pricecharting_name": "Pokemon Generations"},
    "xy10": {"tcg_name": "Fates Collide", "pricecharting_name": "Pokemon Fates Collide"},
    "xy12": {"tcg_name": "Evolutions", "pricecharting_name": "Pokemon Evolutions"},
    "smp": {"tcg_name": "SM Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "sm3": {"tcg_name": "Burning Shadows", "pricecharting_name": "Pokemon Burning Shadows"},
    "sm35": {"tcg_name": "Shining Legends", "pricecharting_name": "Pokemon Shining Legends"},
    "sm9": {"tcg_name": "Team Up", "pricecharting_name": "Pokemon Team Up"},
    "sm10": {"tcg_name": "Unbroken Bonds", "pricecharting_name": "Pokemon Unbroken Bonds"},
    "sm115": {"tcg_name": "Hidden Fates", "pricecharting_name": "Pokemon Hidden Fates"},
    "sm12": {"tcg_name": "Cosmic Eclipse", "pricecharting_name": "Pokemon Cosmic Eclipse"},
    "swshp": {"tcg_name": "SWSH Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "swsh3": {"tcg_name": "Darkness Ablaze", "pricecharting_name": "Pokemon Darkness Ablaze"},
    "swsh35": {"tcg_name": "Champion's Path", "pricecharting_name": "Pokemon Champion's Path"},
    "swsh4": {"tcg_name": "Vivid Voltage", "pricecharting_name": "Pokemon Vivid Voltage"},
    "swsh45": {"tcg_name": "Shining Fates", "pricecharting_name": "Pokemon Shining Fates"},
    "swsh5": {"tcg_name": "Battle Styles", "pricecharting_name": "Pokemon Battle Styles"},
    "swsh6": {"tcg_name": "Chilling Reign", "pricecharting_name": "Pokemon Chilling Reign"},
    "swsh7": {"tcg_name": "Evolving Skies", "pricecharting_name": "Pokemon Evolving Skies"},
    "cel25": {"tcg_name": "Celebrations", "pricecharting_name": "Pokemon Celebrations"},
    "swsh8": {"tcg_name": "Fusion Strike", "pricecharting_name": "Pokemon Fusion Strike"},
    "swsh9": {"tcg_name": "Brilliant Stars", "pricecharting_name": "Pokemon Brilliant Stars"},
    "swsh10": {"tcg_name": "Astral Radiance", "pricecharting_name": "Pokemon Astral Radiance"},
    "pgo": {"tcg_name": "Pokémon GO", "pricecharting_name": "Pokemon Go"},
    "swsh11": {"tcg_name": "Lost Origin", "pricecharting_name": "Pokemon Lost Origin"},
    "swsh12": {"tcg_name": "Silver Tempest", "pricecharting_name": "Pokemon Silver Tempest"},
    "swsh12pt5": {"tcg_name": "Crown Zenith", "pricecharting_name": "Pokemon Crown Zenith"},
    "sv1": {"tcg_name": "Scarlet & Violet", "pricecharting_name": "Pokemon Scarlet & Violet"},
    "svp": {"tcg_name": "Scarlet & Violet Black Star Promos", "pricecharting_name": "Pokemon Promo"},
    "sv2": {"tcg_name": "Paldea Evolved", "pricecharting_name": "Pokemon Paldea Evolved"},
    "sv3": {"tcg_name": "Obsidian Flames", "pricecharting_name": "Pokemon Obsidian Flames"},
    "sv3pt5": {"tcg_name": "151", "pricecharting_name": "Pokemon Scarlet & Violet 151"},
    "sv4": {"tcg_name": "Paradox Rift", "pricecharting_name": "Pokemon Paradox Rift"},
    "sv4pt5": {"tcg_name": "Paldean Fates", "pricecharting_name": "Pokemon Paldean Fates"},
    "sv5": {"tcg_name": "Temporal Forces", "pricecharting_name": "Pokemon Temporal Forces"},
    "sv6": {"tcg_name": "Twilight Masquerade", "pricecharting_name": "Pokemon Twilight Masquerade"},
    "sv6pt5": {"tcg_name": "Shrouded Fable", "pricecharting_name": "Pokemon Shrouded Fable"},
    "sv7": {"tcg_name": "Stellar Crown", "pricecharting_name": "Pokemon Stellar Crown"},
    "sv8": {"tcg_name": "Surging Sparks", "pricecharting_name": "Pokemon Surging Sparks"},
    "sv8pt5": {"tcg_name": "Prismatic Evolutions", "pricecharting_name": "Pokemon Prismatic Evolutions"},
    "dp6": {"tcg_name": "Legends Awakened", "pricecharting_name": "Pokemon Legends Awakened"}
}

# Test cases - mix of cards that should work well and problematic cards
TEST_CASES = [
    # Format: (set_id, card_number, card_name, expected_to_work)
    ("sm3", "150", "Charizard GX", True),  # Burning Shadows Charizard GX - should work well
    ("base1", "4", "Charizard", True),     # Base Set Charizard - should work well
    ("swsh3", "189", "Charizard VMAX", True),  # Darkness Ablaze - should work well
    ("dp6", "27", "Ditto", False),         # Legends Awakened Ditto - known problem card
    ("ex11", "39", "Ditto", False),        # Delta Species Ditto - known problem card
    ("ex11", "40", "Ditto", False),        # Delta Species Ditto (#40) - known problem card
    ("base5", "50", "Charmander", False),  # Team Rocket - might be problematic
    ("sm4", "56", "Bewear", False),        # Crimson Invasion - might be problematic
    ("sv6pt5", "79", "Bewear", False),     # Shrouded Fable - might be problematic
]

class PokemonTCGClient:
    """Client for PokemonTCG.io API"""
    
    BASE_URL = "https://api.pokemontcg.io/v2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key} if api_key else {}
    
    def get_card_by_id(self, card_id: str) -> Dict[str, Any]:
        """Get a card by its ID"""
        url = f"{self.BASE_URL}/cards/{card_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching card by ID {card_id}: {e}")
            return {}
    
    def search_cards(self, query: str) -> List[Dict[str, Any]]:
        """Search for cards using a query string"""
        url = f"{self.BASE_URL}/cards"
        params = {"q": query}
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching cards with query '{query}': {e}")
            return []
    
    def get_card_by_set_and_number(self, set_id: str, number: str) -> Dict[str, Any]:
        """Get a card by set ID and number"""
        query = f'set.id:{set_id} number:{number}'
        cards = self.search_cards(query)
        
        return cards[0] if cards else {}


class PriceChartingClient:
    """Client for PriceCharting API"""
    
    BASE_URL = "https://www.pricecharting.com/api"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
    
    def search_products(self, query: str) -> Dict[str, Any]:
        """Search for products"""
        url = f"{self.BASE_URL}/products"
        params = {
            "t": self.api_token,
            "q": query
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching PriceCharting with query '{query}': {e}")
            return {"status": "error", "error": str(e)}
    
    def get_product_prices(self, product_id: str) -> Dict[str, Any]:
        """Get price details for a product"""
        url = f"{self.BASE_URL}/product"
        params = {
            "t": self.api_token,
            "id": product_id
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting product prices for ID {product_id}: {e}")
            return {"status": "error", "error": str(e)}

    def format_price(self, price_cents: Optional[int]) -> float:
        """Convert price from cents to dollars"""
        if price_cents is None:
            return 0.0
        
        try:
            return float(price_cents) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def direct_lookup(self, card_name: str, set_name: str, card_number: str) -> Dict[str, Any]:
        """Try direct lookup using card name, set name, and number"""
        query = f"pokemon {card_name} {set_name} {card_number}"
        print(f"PriceCharting direct lookup query: '{query}'")
        
        search_results = self.search_products(query)
        
        if search_results.get("status") != "success" or not search_results.get("products"):
            print("No matching products found with direct lookup")
            return {}
        
        # Get first product match
        product = search_results["products"][0]
        product_id = product.get("id")
        
        # Get price details
        return self.get_product_prices(product_id)
    
    def build_search_query(self, card_data: Dict[str, Any]) -> str:
        """Build an optimized search query for a card"""
        card_name = card_data.get("name", "")
        set_data = card_data.get("set", {}) if isinstance(card_data.get("set"), dict) else {}
        set_id = set_data.get("id", "")
        set_name = set_data.get("name", "")
        card_number = card_data.get("number", "")
        
        # Use set mapping if available
        if set_id in SET_MAPPING:
            pricecharting_set_name = SET_MAPPING[set_id]["pricecharting_name"]
        else:
            pricecharting_set_name = set_name
        
        # Detect special card variants
        subtypes = card_data.get("subtypes", [])
        special_type = ""
        for subtype in ["V", "VMAX", "GX", "EX", "V-UNION"]:
            if subtype in subtypes:
                special_type = subtype
                break
        
        # Build query parts
        query_parts = [f"pokemon {card_name}"]
        
        if special_type and special_type not in card_name:
            query_parts.append(special_type)
        
        query_parts.append(pricecharting_set_name)
        
        if card_number:
            query_parts.append(f"{card_number}")
        
        return " ".join(query_parts)
    
    def lookup_card_price(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Look up price data for a card using different strategies"""
        # Strategy 1: Direct lookup
        card_name = card_data.get("name", "")
        set_data = card_data.get("set", {}) if isinstance(card_data.get("set"), dict) else {}
        set_name = set_data.get("name", "")
        card_number = card_data.get("number", "")
        
        direct_result = self.direct_lookup(card_name, set_name, card_number)
        
        if direct_result and direct_result.get("status") == "success":
            return {
                "strategy": "direct_lookup",
                "result": direct_result,
                "query": f"pokemon {card_name} {set_name} {card_number}"
            }
        
        # Strategy 2: Optimized query with set mapping
        optimized_query = self.build_search_query(card_data)
        print(f"PriceCharting optimized query: '{optimized_query}'")
        
        search_results = self.search_products(optimized_query)
        
        if search_results.get("status") != "success" or not search_results.get("products"):
            print("No matching products found with optimized query")
            return {"strategy": "optimized_query", "result": {}, "query": optimized_query}
        
        # Get first product match
        product = search_results["products"][0]
        product_id = product.get("id")
        
        # Get price details
        price_data = self.get_product_prices(product_id)
        
        return {
            "strategy": "optimized_query",
            "result": price_data,
            "query": optimized_query
        }


def format_card_info(card_data: Dict[str, Any]) -> str:
    """Format card information for display"""
    if not card_data:
        return "No card data available"
    
    card_name = card_data.get("name", "Unknown")
    set_data = card_data.get("set", {}) if isinstance(card_data.get("set"), dict) else {}
    set_name = set_data.get("name", "Unknown")
    set_id = set_data.get("id", "Unknown")
    card_number = card_data.get("number", "Unknown")
    rarity = card_data.get("rarity", "Unknown")
    
    subtypes = card_data.get("subtypes", [])
    subtypes_str = ", ".join(subtypes) if subtypes else "None"
    
    output = []
    output.append(f"Card: {card_name}")
    output.append(f"Set: {set_name} ({set_id})")
    output.append(f"Number: {card_number}")
    output.append(f"Rarity: {rarity}")
    output.append(f"Subtypes: {subtypes_str}")
    
    if set_id in SET_MAPPING:
        pc_name = SET_MAPPING[set_id]["pricecharting_name"]
        output.append(f"PriceCharting Set Mapping: {pc_name}")
    
    if card_data.get("images", {}).get("small"):
        output.append(f"Image: {card_data['images']['small']}")
    
    return "\n".join(output)


def format_price_info(price_data: Dict[str, Any]) -> str:
    """Format price information for display"""
    if not price_data or price_data.get("status") != "success":
        return "No price data available"
    
    price_mappings = {
        "loose-price": "Ungraded",
        "cib-price": "Graded 7 or 7.5",
        "new-price": "Graded 8 or 8.5",
        "graded-price": "Graded 9",
        "box-only-price": "Graded 9.5",
        "manual-only-price": "PSA 10",
        "condition-17-price": "CGC 10"
    }
    
    output = []
    output.append(f"Product: {price_data.get('product-name', 'Unknown')}")
    output.append(f"ID: {price_data.get('id', 'Unknown')}")
    output.append(f"Console: {price_data.get('console-name', 'Unknown')}")
    
    output.append("Prices:")
    has_prices = False
    
    for price_key, label in price_mappings.items():
        if price_key in price_data:
            price_cents = price_data[price_key]
            price_dollars = float(price_cents) / 100.0 if price_cents else 0.0
            output.append(f"  {label}: ${price_dollars:.2f}")
            has_prices = True
    
    if not has_prices:
        output.append("  No prices available")
    
    return "\n".join(output)


def run_test_case(pokemon_client: PokemonTCGClient, price_client: PriceChartingClient, 
                 set_id: str, card_number: str, card_name: str, expected_to_work: bool) -> Dict[str, Any]:
    """Run a test case and return results"""
    results = {
        "set_id": set_id,
        "card_number": card_number,
        "card_name": card_name,
        "expected_to_work": expected_to_work,
        "pokemon_tcg": {"success": False, "data": {}},
        "price_charting": {"success": False, "data": {}},
        "overall_success": False
    }
    
    print(f"\n=== Testing {card_name} from {set_id} #{card_number} ===")
    print(f"Expected to work: {'Yes' if expected_to_work else 'No'}")
    
    # Step 1: Get card from PokemonTCG.io
    card_data = pokemon_client.get_card_by_set_and_number(set_id, card_number)
    
    if card_data:
        results["pokemon_tcg"]["success"] = True
        results["pokemon_tcg"]["data"] = card_data
        print("\nPokemonTCG.io Data:")
        print(format_card_info(card_data))
    else:
        print("\nFailed to get card data from PokemonTCG.io")
        return results
    
    # Step 2: Look up price information
    try:
        price_result = price_client.lookup_card_price(card_data)
        price_data = price_result.get("result", {})
        
        if price_data and price_data.get("status") == "success":
            results["price_charting"]["success"] = True
            results["price_charting"]["data"] = price_data
            results["price_charting"]["strategy"] = price_result.get("strategy")
            results["price_charting"]["query"] = price_result.get("query")
            
            print("\nPriceCharting Data:")
            print(f"Strategy: {price_result.get('strategy')}")
            print(f"Query: {price_result.get('query')}")
            print(format_price_info(price_data))
        else:
            print("\nFailed to get price data from PriceCharting")
            print(f"Strategy: {price_result.get('strategy')}")
            print(f"Query: {price_result.get('query')}")
    except Exception as e:
        print(f"\nError during PriceCharting lookup: {e}")
    
    # Overall success
    results["overall_success"] = (results["pokemon_tcg"]["success"] and 
                                 results["price_charting"]["success"])
    
    print(f"\nTest result: {'SUCCESS' if results['overall_success'] else 'FAILURE'}")
    return results


def main():
    """Main test function"""
    print("=== Pokemon TCG and PriceCharting API Test ===\n")
    print(f"Pokemon TCG API Key: {POKEMON_API_KEY[:5]}...{POKEMON_API_KEY[-5:]}")
    print(f"PriceCharting API Key: {PRICECHARTING_API_KEY[:5]}...{PRICECHARTING_API_KEY[-5:]}")
    
    # Initialize API clients
    pokemon_client = PokemonTCGClient(POKEMON_API_KEY)
    price_client = PriceChartingClient(PRICECHARTING_API_KEY)
    
    # Run tests and collect results
    results = []
    for test_case in TEST_CASES:
        set_id, card_number, card_name, expected_to_work = test_case
        
        # Add a delay between tests to avoid rate limits
        if results:  # Don't delay before the first test
            time.sleep(1)
        
        result = run_test_case(pokemon_client, price_client, set_id, card_number, card_name, expected_to_work)
        results.append(result)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Tests run: {len(results)}")
    successful_tests = sum(1 for r in results if r["overall_success"])
    print(f"Successful tests: {successful_tests} / {len(results)}")
    
    expected_success = sum(1 for r in results if r["overall_success"] == r["expected_to_work"])
    print(f"Tests matching expectations: {expected_success} / {len(results)}")
    
    # Save results to file
    output_file = "pokemon_api_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())