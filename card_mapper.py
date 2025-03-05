"""
CardMapper module for mapping between different Pokemon card data formats
and finding best matches between databases.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class CardMapper:
    """
    Helper class for matching cards between different data sources
    """
    
    # Confidence thresholds for matches
    MIN_CONFIDENCE_REQUIRED = 1  # Minimum confidence needed for a match (0-3)
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text for better matching - remove special characters and normalize spaces
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Replace special characters with spaces
        text = re.sub(r'[^a-z0-9]', ' ', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings (0.0 to 1.0)
        Uses a simple token-based approach
        """
        if not str1 or not str2:
            return 0.0
            
        # Clean and tokenize
        tokens1 = set(CardMapper.clean_text(str1).split())
        tokens2 = set(CardMapper.clean_text(str2).split())
        
        # Calculate Jaccard similarity
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def build_search_query(card_data: Dict[str, Any]) -> str:
        """
        Build an optimized search query for PriceCharting
        """
        # Extract card information
        card_name = card_data.get('name', '')
        
        # Handle nested set data or flat structure
        set_data = card_data.get('set', {}) if isinstance(card_data.get('set'), dict) else {}
        set_id = set_data.get('id', '') if set_data else card_data.get('set_id', '')
        set_name = set_data.get('name', '') if set_data else card_data.get('set', '')
        
        card_number = card_data.get('number', '')
        subtypes = card_data.get('subtypes', [])
        
        # Detect special variants
        special_type = ""
        for subtype in ["V", "VMAX", "GX", "EX", "V-UNION"]:
            if subtype in subtypes:
                special_type = subtype
                break
        
        # Build query parts
        query_parts = ["pokemon", card_name]
        
        # Add special type if not in card name
        if special_type and special_type.lower() not in card_name.lower():
            query_parts.append(special_type)
        
        # Add set name
        if set_name:
            query_parts.append(set_name)
        
        # Add card number for certain sets that need it
        if card_number and set_id in ["dp6", "ex11"]:  # Add problematic sets here
            query_parts.append(f"#{card_number}")
        
        return " ".join(query_parts)
    
    @staticmethod
    def find_best_match(card_data: Dict[str, Any], products: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
        """
        Find the best matching product from search results based on similarity
        
        Args:
            card_data: Card data from Pokemon TCG API
            products: List of products from PriceCharting API
            
        Returns:
            Tuple of (best_match, confidence_level)
            Confidence levels: 0=None, 1=Low, 2=Medium, 3=High
        """
        if not products:
            return None, 0
            
        card_name = card_data.get('name', '')
        card_number = card_data.get('number', '')
        
        # Get set info
        set_data = card_data.get('set', {}) if isinstance(card_data.get('set'), dict) else {}
        set_name = set_data.get('name', '') if set_data else card_data.get('set', '')
        set_id = set_data.get('id', '') if set_data else card_data.get('set_id', '')
        
        # Handle special card types
        subtypes = card_data.get('subtypes', [])
        special_type = None
        for subtype in ["V", "VMAX", "GX", "EX", "V-UNION"]:
            if subtype in subtypes:
                special_type = subtype
                break
        
        best_match = None
        best_confidence = 0
        best_similarity = 0
        
        for product in products:
            product_name = product.get('name', '')
            console_name = product.get('console-name', '')
            
            # Skip if product is not a Pokemon card
            if 'pokemon' not in product_name.lower() and 'pokemon' not in console_name.lower():
                continue
                
            # Calculate name similarity
            base_similarity = CardMapper.calculate_similarity(card_name, product_name)
            
            # Check for card number in product name
            has_matching_number = False
            if card_number and f"#{card_number}" in product_name:
                has_matching_number = True
                base_similarity += 0.1  # Bonus for matching card number
            
            # Check for set name in product
            set_similarity = CardMapper.calculate_similarity(set_name, console_name)
            
            # Calculate final similarity score
            similarity = (base_similarity * 0.7) + (set_similarity * 0.3)
            
            # Determine confidence level
            confidence = 0
            if similarity >= 0.8:
                confidence = 3  # High
            elif similarity >= 0.6:
                confidence = 2  # Medium
            elif similarity >= 0.4:
                confidence = 1  # Low
                
            # Boost confidence if card number is explicitly matched
            if has_matching_number and confidence < 3:
                confidence += 1
                
            # Special handling for problematic sets
            if set_id in ["dp6", "ex11"] and card_number in product_name:
                confidence = max(confidence, 2)  # At least medium confidence
                
            # Special handling for identical names
            if card_name.lower() == product_name.lower().replace('pokemon ', ''):
                confidence = max(confidence, 3)
                
            # Update best match if this is better
            if confidence > best_confidence or (confidence == best_confidence and similarity > best_similarity):
                best_match = product
                best_confidence = confidence
                best_similarity = similarity
                
        logger.debug(f"Best match for {card_name}: {best_match['name'] if best_match else 'None'} (Confidence: {best_confidence})")
        return best_match, best_confidence