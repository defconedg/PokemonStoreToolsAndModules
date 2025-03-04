import requests
import logging
import random
import re
from typing import Dict, List, Any, Optional
from card_mapper import CardMapper

logger = logging.getLogger(__name__)

class PriceChartingClient:
    """
    Client for interacting with the PriceCharting API
    Documentation: https://www.pricecharting.com/api-documentation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with optional API key"""
        self.api_key = api_key
        self.card_mapper = CardMapper()
    
    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for products in PriceCharting
        
        Args:
            query: Search query string
            
        Returns:
            List of matching products
        """
        if not self.api_key:
            logger.warning("No PriceCharting API key provided. Using generated data.")
            return self._generate_test_products(query)
            
        try:
            logger.debug(f"Searching PriceCharting with query: '{query}'")
            url = f"https://www.pricecharting.com/api/products?t={self.api_key}&q={query}"
            response = requests.get(url)
            response.raise_for_status()
            
            products = response.json().get('products', [])
            logger.debug(f"Found {len(products)} products for query '{query}'")
            return products
            
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {str(e)}")
            return self._generate_test_products(query)
    
    def get_product_prices(self, product_id: str) -> Dict[str, Any]:
        """
        Get detailed pricing for a specific product
        
        Args:
            product_id: The ID of the product
            
        Returns:
            Dictionary with pricing data
        """
        if not self.api_key:
            logger.warning("No PriceCharting API key provided. Using generated data.")
            return self._generate_test_prices(product_id)
            
        try:
            url = f"https://www.pricecharting.com/api/product?t={self.api_key}&id={product_id}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Convert cents to dollars
            pricing = self._convert_prices_to_dollars(data)
            
            # Add product URL
            pricing['url'] = f"https://www.pricecharting.com/game/pokemon-card/{product_id}"
            
            return pricing
        except Exception as e:
            logger.error(f"Error getting prices for product {product_id}: {str(e)}")
            return self._generate_test_prices(product_id)
    
    def get_card_prices_by_tcgdata(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get pricing data for a Pokémon card using the full TCG API card data
        
        Args:
            card_data: Full card data from Pokemon TCG API
            
        Returns:
            Dictionary with pricing data
        """
        # Get the card name and set
        card_name = card_data.get('name', '')
        set_name = card_data.get('set', {}).get('name', '') if isinstance(card_data.get('set'), dict) else card_data.get('set', '')
        set_id = card_data.get('set', {}).get('id', '') if isinstance(card_data.get('set'), dict) else ''
        number = card_data.get('number', '')
        
        logger.info(f"Getting PriceCharting data for '{card_name}' (#{number}) from '{set_name}'")
        
        # Use our mapper to build an optimized search query
        search_query = CardMapper.build_search_query(card_data)
        logger.debug(f"Built search query: '{search_query}'")
        
        # Search for products
        products = self.search_products(search_query)
        
        # Find best match using improved algorithm
        if products:
            best_match, confidence = CardMapper.find_best_match(card_data, products)
            
            if best_match:
                confidence_labels = ["Unconfirmed", "Low", "Medium", "High"]
                product_name = best_match.get('name', 'Unknown')
                product_id = best_match.get('id')
                
                logger.info(f"Found PriceCharting product ID: {product_id}")
                confidence_msg = f" (Confidence: {confidence_labels[confidence]})" if confidence > 0 else ""
                logger.debug(f"Product match: {product_name}{confidence_msg}")
                
                try:
                    pricing_data = self.get_product_prices(product_id)
                    # Add the matched product details for verification
                    pricing_data['product'] = best_match
                    pricing_data['match_confidence'] = confidence
                    
                    return pricing_data
                except Exception as e:
                    logger.error(f"Error getting prices for {product_name}: {str(e)}")
            else:
                logger.warning(f"No suitable product match found for {card_name} (#{number})")
        else:
            logger.warning(f"No products found for '{search_query}'")
            
            # Try alternative search with just card name and number
            alt_query = f"{card_name} pokemon #{number}"
            logger.debug(f"Trying alternative query: '{alt_query}'")
            products = self.search_products(alt_query)
            
            if products:
                best_match, confidence = CardMapper.find_best_match(card_data, products)
                
                if best_match:
                    product_name = best_match.get('name', 'Unknown')
                    product_id = best_match.get('id')
                    
                    logger.info(f"Found PriceCharting product ID: {product_id} (alternative search)")
                    
                    pricing_data = self.get_product_prices(product_id)
                    pricing_data['product'] = best_match
                    pricing_data['match_confidence'] = confidence
                    
                    return pricing_data
            
            logger.warning(f"No products found for alternative query '{alt_query}'")
        
        # Fallback to test data if we couldn't get real prices
        return self._generate_test_card_prices(card_name, set_name)
        
    def get_card_prices(self, card_name: str, set_name: str, number: str = None, variant: str = None) -> Dict[str, Any]:
        """
        Get pricing data for a Pokémon card by name and set (legacy method)
        
        Args:
            card_name: Name of the card
            set_name: Name of the set
            number: Card number in the set (optional)
            variant: Card variant (e.g., holofoil, reverse holofoil) (optional)
            
        Returns:
            Dictionary with pricing data
        """
        # Build a search query
        query_parts = [card_name, "pokemon", set_name]
        
        if number:
            query_parts.append(f"#{number}")
            
        if variant:
            query_parts.append(variant)
            
        search_query = " ".join(query_parts)
        
        # Search for products
        products = self.search_products(search_query)
        
        if not products:
            logger.warning(f"No products found for '{search_query}'")
            return self._generate_test_card_prices(card_name, set_name)
            
        product_id = products[0].get('id')
        pricing_data = self.get_product_prices(product_id)
        
        # Add the matched product details for verification
        pricing_data['product'] = products[0]
        
        return pricing_data
    
    def _convert_prices_to_dollars(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert prices from cents to dollars and extract grading information
        
        Args:
            data: Raw pricing data from API
            
        Returns:
            Processed pricing data with dollars
        """
        result = {'prices': {}}
        
        # Convert basic prices
        for key in ['loose-price', 'complete-price', 'new-price', 'graded-price']:
            if key in data and data[key] is not None:
                clean_key = key.replace('-price', '')
                result['prices'][clean_key] = data[key] / 100
        
        # Extract grading-specific prices
        grades = {}
        for key, value in data.items():
            # Look for graded prices like psa-10-price, bgs-9.5-price, etc.
            if '-price' in key and key != 'graded-price' and value is not None:
                grading_info = key.replace('-price', '')
                grades[grading_info] = value / 100
        
        # Add grading information if available
        if grades:
            result['prices']['graded_variants'] = grades
            
            # Add PSA grades if available
            psa_grades = {k: v for k, v in grades.items() if k.startswith('psa')}
            if psa_grades:
                result['prices']['psa_grades'] = psa_grades
                
            # Add BGS grades if available
            bgs_grades = {k: v for k, v in grades.items() if k.startswith('bgs')}
            if bgs_grades:
                result['prices']['bgs_grades'] = bgs_grades
                
            # Add CGC grades if available
            cgc_grades = {k: v for k, v in grades.items() if k.startswith('cgc')}
            if cgc_grades:
                result['prices']['cgc_grades'] = cgc_grades
        
        return result
    
    def _generate_test_products(self, query: str) -> List[Dict[str, Any]]:
        """Generate test products for development/testing"""
        # Use query as seed for consistency
        seed = sum(ord(c) for c in query)
        random.seed(seed)
        
        product_id = f"pokemon-{query.lower().replace(' ', '-')}"
        
        return [{
            'id': product_id,
            'name': query,
            'console-name': 'Pokemon Card',
            'url': f"https://www.pricecharting.com/game/pokemon-card/{product_id}"
        }]
    
    def _generate_test_prices(self, product_id: str) -> Dict[str, Any]:
        """Generate test pricing data for development/testing"""
        # Use product_id as seed for consistency
        seed = sum(ord(c) for c in product_id)
        random.seed(seed)
        
        # Base price depends on product_id characteristics
        if 'rare' in product_id or 'holo' in product_id:
            base_price = random.uniform(5.0, 50.0)
        elif 'ultra' in product_id or 'secret' in product_id:
            base_price = random.uniform(20.0, 150.0)
        else:
            base_price = random.uniform(0.5, 10.0)
            
        # Generate more realistic graded prices
        result = {
            'prices': {
                'loose': round(base_price, 2),
                'graded': round(base_price * 3, 2),
                'graded_variants': {
                    'psa-10': round(base_price * 10, 2),
                    'psa-9': round(base_price * 5, 2),
                    'psa-8': round(base_price * 2.5, 2),
                    'bgs-9.5': round(base_price * 8, 2),
                    'cgc-10': round(base_price * 9, 2)
                },
                'psa_grades': {
                    'psa-10': round(base_price * 10, 2),
                    'psa-9': round(base_price * 5, 2),
                    'psa-8': round(base_price * 2.5, 2)
                }
            },
            'url': f"https://www.pricecharting.com/game/pokemon-card/{product_id}"
        }
        
        return result
    
    def _generate_test_card_prices(self, card_name: str, set_name: str) -> Dict[str, Any]:
        """Generate test card prices based on card and set name"""
        product_id = f"{card_name.lower().replace(' ', '-')}-{set_name.lower().replace(' ', '-')}"
        return self._generate_test_prices(product_id)