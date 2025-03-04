#!/usr/bin/env python
"""
Utility to compare card data between PokemonTCG.io and PriceCharting APIs
Helps diagnose specific card matching issues
"""
import os
import json
import logging
import time
from pprint import pprint
from dotenv import load_dotenv
from price_charting import PriceChartingClient
from pokemontcg_client import PokemonTCGClient
from card_mapper import CardMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class CardComparisonTool:
    def __init__(self):
        """Initialize API clients"""
        self.pokemontcg_key = os.environ.get('POKE_API_KEY')
        self.pricecharting_key = os.environ.get('PRICECHARTING_API_KEY')
        
        self.pokemontcg = PokemonTCGClient(self.pokemontcg_key)
        self.pricecharting = PriceChartingClient(self.pricecharting_key)
    
    def get_tcg_card(self, card_id):
        """Get card data from PokemonTCG.io"""
        try:
            logger.info(f"Fetching card {card_id} from PokemonTCG.io API...")
            card_data = self.pokemontcg.get_card(card_id)
            return card_data
        except Exception as e:
            logger.error(f"Error fetching card {card_id} from PokemonTCG.io: {str(e)}")
            return None
    
    def search_pricecharting(self, card_data):
        """Search for card in PriceCharting"""
        try:
            card_name = card_data.get('name', '')
            set_name = card_data.get('set', {}).get('name', '')
            card_number = card_data.get('number', '')
            
            logger.info(f"Searching for '{card_name}' (#{card_number}) from '{set_name}' in PriceCharting...")
            
            # Use our card mapper to build an optimized search query
            search_query = CardMapper.build_search_query(card_data)
            logger.info(f"Search query: '{search_query}'")
            
            # Search for the card
            results = self.pricecharting.search_products(search_query)
            
            # Try to find the best match
            best_match, confidence = CardMapper.find_best_match(card_data, results)
            
            return {
                'search_query': search_query,
                'search_results': results,
                'best_match': best_match,
                'confidence': confidence,
                'confidence_label': ['None', 'Low', 'Medium', 'High'][confidence]
            }
        except Exception as e:
            logger.error(f"Error searching PriceCharting: {str(e)}")
            return None
    
    def analyze_card(self, card_id, additional_queries=None):
        """Analyze a specific card across both APIs"""
        print(f"\n{'=' * 80}\nANALYZING CARD: {card_id}\n{'=' * 80}\n")
        
        # Get card data from PokemonTCG.io
        card_data = self.get_tcg_card(card_id)
        if not card_data:
            print(f"Could not fetch card {card_id} from PokemonTCG.io API")
            return
        
        # Print basic card info
        print(f"CARD NAME: {card_data.get('name')}")
        print(f"SET: {card_data.get('set', {}).get('name')} (ID: {card_data.get('set', {}).get('id')})")
        print(f"NUMBER: {card_data.get('number')}")
        print(f"RARITY: {card_data.get('rarity')}")
        if 'tcgplayer' in card_data and 'prices' in card_data['tcgplayer']:
            print(f"VARIANTS: {', '.join(card_data['tcgplayer']['prices'].keys())}")
            
        # Get standardized identifiers
        std_name = CardMapper.standardize_card_name(card_data.get('name', ''))
        std_set = CardMapper.standardize_set_name(card_data.get('set', {}).get('name', ''))
        print(f"\nSTANDARDIZED NAME: '{std_name}'")
        print(f"STANDARDIZED SET: '{std_set}'")
        
        # Check if we have set mapping
        set_id = card_data.get('set', {}).get('id', '')
        mapped_set = CardMapper.get_set_id_mapping(set_id)
        print(f"SET ID MAPPING: {set_id} -> {mapped_set if mapped_set else 'NOT MAPPED'}")
        
        # Search for card in PriceCharting
        print("\nSEARCHING PRICECHARTING...")
        pc_results = self.search_pricecharting(card_data)
        
        if pc_results:
            print(f"SEARCH QUERY: '{pc_results['search_query']}'")
            print(f"RESULTS: {len(pc_results['search_results'])} products found")
            
            if pc_results['best_match']:
                print(f"\nBEST MATCH: {pc_results['best_match'].get('name')}")
                print(f"ID: {pc_results['best_match'].get('id')}")
                print(f"CONFIDENCE: {pc_results['confidence_label']} ({pc_results['confidence']})")
                
                # Get pricing data for the best match
                try:
                    print("\nGETTING PRICING DATA...")
                    pricing_data = self.pricecharting.get_product_prices(pc_results['best_match'].get('id'))
                    
                    print("PRICES:")
                    if 'prices' in pricing_data:
                        for key, value in pricing_data['prices'].items():
                            if isinstance(value, dict):
                                print(f"  {key}:")
                                for k, v in value.items():
                                    print(f"    {k}: ${v}")
                            else:
                                print(f"  {key}: ${value}")
                except Exception as e:
                    print(f"Error getting pricing data: {str(e)}")
            else:
                print("\nNO MATCH FOUND")
            
            # Print all results for reference
            print(f"\nALL SEARCH RESULTS ({len(pc_results['search_results'])}):")
            for i, result in enumerate(pc_results['search_results'][:10]):  # Show first 10 results
                print(f"{i+1}. {result.get('name', 'Unknown')} (ID: {result.get('id', 'Unknown')})")
        else:
            print("Failed to search PriceCharting API")
        
        # Try additional queries if specified
        if additional_queries:
            print("\nTRYING ADDITIONAL QUERIES:")
            for query in additional_queries:
                print(f"\nQUERY: '{query}'")
                try:
                    results = self.pricecharting.search_products(query)
                    print(f"RESULTS: {len(results)} products found")
                    
                    for i, result in enumerate(results[:5]):  # Show first 5 results
                        print(f"{i+1}. {result.get('name', 'Unknown')} (ID: {result.get('id', 'Unknown')})")
                except Exception as e:
                    print(f"Error with query: {str(e)}")

def main():
    """Main function"""
    tool = CardComparisonTool()
    
    # Define problem cards to analyze
    problem_cards = [
        # Format: card_id, [additional_queries]
        ("sv6pt5-79", ["Bewear 79 Shrouded Fable", "Bewear pokemon"]),  # Bewear from Shrouded Fable
        ("xy10-55", ["Umbreon EX 55", "Umbreon EX Fates Collide"]),     # Umbreon EX from Fates Collide
        ("swsh7-231", ["Full Face Guard 231", "Full Face Guard Evolving Skies"]),  # Full Face Guard
        ("sv3pt5-1", ["Bulbasaur 1", "Bulbasaur Pokemon 151"]),  # Bulbasaur from Pokemon 151
    ]
    
    # Analyze each card
    for card_id, additional_queries in problem_cards:
        try:
            tool.analyze_card(card_id, additional_queries)
            print("\n" + "-" * 40 + "\n")  # Separator between cards
            time.sleep(1)  # Avoid rate limits
        except Exception as e:
            logger.error(f"Error analyzing card {card_id}: {str(e)}")

if __name__ == "__main__":
    main()
