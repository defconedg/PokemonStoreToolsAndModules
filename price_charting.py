import requests
import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from card_mapper import CardMapper

logger = logging.getLogger(__name__)

class PriceChartingClient:
    """
    Client for interacting with PriceCharting API
    """
    
    BASE_URL = "https://www.pricecharting.com"
    SEARCH_ENDPOINT = "/api/products"
    PRODUCT_ENDPOINT = "/api/product"
    
    # Default prices to use when no match is found
    DEFAULT_PRICES = {
        "loose_price": 0.0,
        "graded_price": 0.0,
        "complete_price": 0.0
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with optional API key"""
        self.api_key = api_key
        
    def format_price(self, price_in_pennies):
        """Format price from pennies to dollars"""
        if price_in_pennies is None:
            return 0.0
        
        try:
            return float(price_in_pennies) / 100.0
        except (ValueError, TypeError):
            return 0.0
    
    def direct_card_lookup(self, card_name: str, set_name: str = None, card_number: str = None) -> Dict[str, Any]:
        """
        Directly query the PriceCharting API for a specific card
        
        Args:
            card_name: Name of the card
            set_name: Name of the set (optional)
            card_number: Card number in the set (optional)
            
        Returns:
            Dictionary with price data
        """
        # Try multiple query variations to increase chance of success
        query_variations = []
        
        # Variation 1: Standard format
        if set_name and card_name:
            standard_query = f"pokemon {card_name} {set_name}"
            if card_number:
                standard_query += f" #{card_number}"
            query_variations.append(standard_query)
        
        # Variation 2: With number but no "pokemon" prefix
        if set_name and card_name and card_number:
            query_variations.append(f"{card_name} {set_name} #{card_number}")
        
        # Variation 3: Just name and set
        if set_name and card_name:
            query_variations.append(f"pokemon {card_name} {set_name}")
        
        # Variation 4: Just name and number
        if card_name and card_number:
            query_variations.append(f"pokemon {card_name} #{card_number}")
        
        # Variation 5: Just name with pokemon prefix
        if card_name:
            query_variations.append(f"pokemon {card_name}")
        
        # Try each query variation until we find a match
        for query in query_variations:
            logger.debug(f"Trying direct lookup query: '{query}'")
            
            params = {"q": query}
            if self.api_key:
                params["token"] = self.api_key
                
            try:
                response = requests.get(
                    f"{self.BASE_URL}{self.PRODUCT_ENDPOINT}",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("status") == "success":
                    logger.info(f"Direct lookup success with query: '{query}'")
                    # Extract and format prices
                    prices = {
                        "loose_price": self.format_price(data.get("loose-price")),      # Ungraded card 
                        "graded_price": self.format_price(data.get("graded-price")),    # PSA 9
                        "psa10_price": self.format_price(data.get("manual-only-price")), # PSA 10
                        "grade_8_price": self.format_price(data.get("new-price")),      # PSA 8 or 8.5
                        "grade_7_price": self.format_price(data.get("cib-price")),      # PSA 7 or 7.5
                        "bgs10_price": self.format_price(data.get("box-only-price")),   # BGS 9.5
                        "cgc10_price": self.format_price(data.get("condition-17-price")), # CGC 10
                        "sgc10_price": self.format_price(data.get("condition-18-price")) # SGC 10
                    }
                    
                    return {
                        "product_id": data.get("id"),
                        "product_name": data.get("product-name"),
                        "set_name": data.get("console-name"),
                        "prices": prices,
                        "confidence": 3,  # High confidence for direct lookup
                        "confidence_label": "High (Direct)",
                        "direct_lookup": True
                    }
            except Exception as e:
                logger.debug(f"Direct lookup attempt failed for query '{query}': {str(e)}")
                continue
        
        logger.warning(f"All direct lookup attempts failed for {card_name} ({set_name} #{card_number})")
        return {}
    
    def search_products(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for products matching the query
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        params = {
            "q": query,
            "limit": limit,
            "t": "pokemon",  # Restrict to Pokemon category
        }
        
        if self.api_key:
            params["token"] = self.api_key
            
        try:
            response = requests.get(
                f"{self.BASE_URL}{self.SEARCH_ENDPOINT}",
                params=params
            )
            response.raise_for_status()
            
            results = response.json().get("products", [])
            logger.debug(f"Found {len(results)} results for query '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            return []
            
    def get_product_prices(self, product_id: str) -> Dict[str, Any]:
        """
        Get prices for a specific product
        
        Args:
            product_id: Product ID
            
        Returns:
            Dictionary with price data
        """
        params = {}
        if self.api_key:
            params["token"] = self.api_key
            
        try:
            response = requests.get(
                f"{self.BASE_URL}{self.PRODUCT_ENDPOINT}/{product_id}",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {str(e)}")
            return {}
            
    def get_card_prices(self, card_data: Dict[str, Any], retries: int = 2) -> Dict[str, Any]:
        """
        Get prices for a Pokemon card by searching and finding the best match
        
        Args:
            card_data: Card data from PokemonTCG.io API
            retries: Number of retries with different search strategies
            
        Returns:
            Dictionary with price data and match information
        """
        # Extract basic card info for logging
        card_name = card_data.get('name', 'Unknown')
        card_number = card_data.get('number', '')
        set_name = card_data.get('set', {}).get('name', '') if isinstance(card_data.get('set'), dict) else ''
        card_id = card_data.get('id', '')
        
        logger.info(f"Getting PriceCharting data for '{card_name}' (#{card_number}) from '{set_name}'")
        
        # Special case manual overrides for known problematic cards
        MANUAL_PRICE_OVERRIDES = {
            "dp6-27": {
                "product_id": "10-46940",  # If you know the actual product ID
                "product_name": "Ditto (Legends Awakened)",
                "prices": {
                    "loose_price": 3.95,
                    "graded_price": 12.85,
                    "complete_price": 0.0
                }
            }
        }
        
        # Check if we have a manual override
        if card_id in MANUAL_PRICE_OVERRIDES:
            logger.info(f"Using manual price override for {card_name} (#{card_number})")
            override_data = MANUAL_PRICE_OVERRIDES[card_id]
            
            # Create result with override data
            result = {
                "search_query": f"MANUAL OVERRIDE: {card_name} #{card_number}",
                "products_found": 1,
                "confidence": 3,  # High confidence for manual override
                "confidence_label": "High (Manual)",
                "product_id": override_data.get("product_id", "manual"),
                "product_name": override_data.get("product_name", f"{card_name} (Manual Override)"),
                "prices": override_data.get("prices", self.DEFAULT_PRICES.copy())
            }
            return result
        
        # First attempt: Try direct lookup
        direct_result = self.direct_card_lookup(
            card_name=card_name,
            set_name=set_name,
            card_number=card_number
        )
        
        if direct_result:
            logger.info(f"Successfully found direct match for {card_name} (#{card_number})")
            return direct_result
        
        # If direct lookup fails, fall back to search and match approach
        logger.debug(f"Direct lookup failed, trying search and match for {card_name}")
        
        # Build search query
        search_query = CardMapper.build_search_query(card_data)
        
        # Special handling for specific problematic sets
        set_id = card_data.get('set', {}).get('id') if isinstance(card_data.get('set'), dict) else None
        if set_id in ["dp6", "ex11"]:
            # For problematic sets, always include card number in search
            if card_number and card_number not in search_query:
                search_query = f"{search_query} #{card_number}"
        
        # First search attempt with primary search strategy
        products = self.search_products(search_query)
        
        if not products and retries > 0:
            # Try a simpler query with just the name and set
            simple_query = f"{card_name} {set_name}"
            logger.debug(f"No results found, trying simpler query: '{simple_query}'")
            products = self.search_products(simple_query)
            retries -= 1
            
            # If still no results and we have retries left, try name only
            if not products and retries > 0:
                name_only_query = card_name
                logger.debug(f"Still no results, trying name-only query: '{name_only_query}'")
                products = self.search_products(name_only_query)
        
        # Find the best match
        best_match, confidence = CardMapper.find_best_match(card_data, products)
        
        # Special handling for certain cards - if no good match found
        if (not best_match or confidence < CardMapper.MIN_CONFIDENCE_REQUIRED) and card_id:
            if card_id.startswith("dp6-"):  # Diamond & Pearl: Legends Awakened
                # Try with more specific search
                specific_query = f"{card_name} Legends Awakened #{card_number}"
                logger.debug(f"Trying specialized query for DP card: '{specific_query}'")
                products = self.search_products(specific_query)
                best_match, confidence = CardMapper.find_best_match(card_data, products)
        
        # Build result dictionary
        result = {
            "search_query": search_query,
            "products_found": len(products),
            "confidence": confidence,
            "confidence_label": ["None", "Low", "Medium", "High"][confidence],
            "prices": self.DEFAULT_PRICES.copy()
        }
        
        # Get prices if we found a match with sufficient confidence
        if best_match and confidence >= CardMapper.MIN_CONFIDENCE_REQUIRED:
            product_id = best_match.get("id")
            result["product_id"] = product_id
            result["product_name"] = best_match.get("name", "")
            
            # Fetch full price data
            price_data = self.get_product_prices(product_id)
            
            if price_data:
                # Extract pricing information
                result["prices"] = {
                    "loose_price": self.format_price(price_data.get("loose-price", 0.0)),
                    "graded_price": self.format_price(price_data.get("graded-price", 0.0)),
                    "complete_price": self.format_price(price_data.get("complete-price", 0.0)),
                    "psa10_price": self.format_price(price_data.get("manual-only-price", 0.0))
                }
                
                # Include raw price data for debugging
                result["raw_price_data"] = price_data
        else:
            # If confidence is too low or no match found
            logger.warning(f"No suitable product match found for {card_name} (#{card_number})")
            
            # For debugging purposes, include the top result even if confidence is low
            if best_match:
                result["rejected_match"] = {
                    "id": best_match.get("id"),
                    "name": best_match.get("name"),
                    "reason": f"Confidence too low: {confidence} < {CardMapper.MIN_CONFIDENCE_REQUIRED}"
                }
        
        return result
        
    # Alias to maintain backwards compatibility with existing code
    get_card_prices_by_tcgdata = get_card_prices