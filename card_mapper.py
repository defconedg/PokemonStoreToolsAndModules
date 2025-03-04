import logging
import re
import time
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class CardMapper:
    """
    Utility class for mapping and standardizing card identifiers between
    different APIs (PokemonTCG.io, PriceCharting, etc.)
    """
    
    # Set code mappings between APIs
    SET_CODE_MAPPINGS = {
        # PokemonTCG.io code -> PriceCharting identifier
        "swsh1": "sword-shield",
        "swsh2": "sword-shield-rebel-clash",
        "swsh3": "sword-shield-darkness-ablaze",
        "swsh4": "sword-shield-vivid-voltage",
        "swsh5": "sword-shield-battle-styles",
        "swsh6": "sword-shield-chilling-reign",
        "swsh7": "sword-shield-evolving-skies",
        "swsh8": "sword-shield-fusion-strike",
        "swsh9": "sword-shield-brilliant-stars",
        "swsh10": "sword-shield-astral-radiance",
        "swsh11": "sword-shield-lost-origin",
        "swsh12": "sword-shield-silver-tempest",
        "swsh12pt5": "crown-zenith",
        "sv1": "scarlet-violet",
        "sv2": "scarlet-violet-paldea-evolved",
        "sv3": "scarlet-violet-obsidian-flames",
        "sv3pt5": "pokemon-151",
        "sv4": "scarlet-violet-paradox-rift",
        "sv5": "scarlet-violet-temporal-forces",
        "sv6": "scarlet-violet-mask-of-change",
        "sv6pt5": "shrouded-fable",
        "sv8pt5": "prismatic-evolutions",
        # Add more mappings as needed
    }
    
    # Common name variations between APIs
    NAME_VARIATIONS = {
        "gx": ["gx", "g x", "g.x.", "gx card"],
        "vmax": ["vmax", "v max", "v-max", "vmax card"],
        "vstar": ["vstar", "v star", "v-star", "vstar card"],
        "v-union": ["v union", "v-union", "vunion"],
        "ex": [" ex", "-ex", " e.x.", " EX", "ex card"],
        "full art": ["full art", "full-art", "fullart", "fa"],
    }
    
    # Maximum number of products to check for matching
    MAX_PRODUCTS_TO_CHECK = 20
    
    # Rate limiting to avoid excessive API calls
    REQUEST_DELAY = 0.1  # seconds between requests
    
    @staticmethod
    def standardize_set_name(set_name: str) -> str:
        """Convert set name to a standardized format for matching"""
        if not set_name:
            return ""
        # Remove special characters and standardize spacing
        standardized = set_name.lower()
        standardized = re.sub(r'[^a-z0-9\s]', '', standardized)
        standardized = re.sub(r'\s+', '-', standardized)
        return standardized
    
    @staticmethod
    def standardize_card_name(card_name: str) -> str:
        """Convert card name to a standardized format for matching"""
        if not card_name:
            return ""
        # Lower case and remove special characters
        standardized = card_name.lower()
        standardized = re.sub(r'[^a-z0-9\s]', ' ', standardized)
        standardized = re.sub(r'\s+', ' ', standardized).strip()
        return standardized
    
    @staticmethod
    def build_search_query(card_data: Dict[str, Any]) -> str:
        """
        Build an optimized search query for PriceCharting based on PokemonTCG.io data
        
        Args:
            card_data: Card data from PokemonTCG.io API
            
        Returns:
            Search query string optimized for PriceCharting
        """
        name = card_data.get('name', '')
        set_name = card_data.get('set', {}).get('name', '') if isinstance(card_data.get('set'), dict) else card_data.get('set', '')
        card_number = card_data.get('number', '')
        rarity = card_data.get('rarity', '')
        
        # Check if card has special variants
        tcgplayer_data = card_data.get('tcgplayer', {}) or {}
        prices = tcgplayer_data.get('prices', {}) or {}
        has_holo = bool(prices.get('holofoil'))
        has_reverse_holo = bool(prices.get('reverseHolofoil'))
        
        # Extract card variant from subtypes if applicable
        subtypes = card_data.get('subtypes', [])
        variant = ""
        for subtype in subtypes:
            if subtype and isinstance(subtype, str) and subtype.lower() in ["vmax", "vstar", "v", "ex", "gx"]:
                variant = subtype
                break
        
        # Build the query
        query_parts = []
        query_parts.append(name)
        
        # Add variant to search query if it exists
        if variant and name:
            # Don't add it if it's already in the name
            if variant.lower() not in name.lower():
                query_parts.append(variant)
        
        # Add set name
        if set_name:
            query_parts.append(set_name)
        
        # Add rarity for better matching if it's special
        if rarity and any(r in rarity.lower() for r in ['ultra', 'secret', 'rainbow', 'gold']):
            query_parts.append(rarity)
            
        # Add holofoil or reverse holofoil if applicable
        if has_holo:
            query_parts.append("holofoil")
        elif has_reverse_holo:
            query_parts.append("reverse holofoil")
        
        # Add card number for better accuracy
        if card_number:
            query_parts.append(f"#{card_number}")
        
        return " ".join(query_parts)
    
    @classmethod
    def verify_match(cls, card_data: Dict[str, Any], pricecharting_result: Dict[str, Any]) -> bool:
        """
        Verify if the PriceCharting result matches the PokemonTCG.io card
        
        Args:
            card_data: Card data from PokemonTCG.io API
            pricecharting_result: Search result from PriceCharting API
            
        Returns:
            True if it's a confirmed match, False otherwise
        """
        # Check if we have valid data to compare
        if not pricecharting_result or not card_data:
            return False
            
        # Extract key information from both sources
        tcg_name = cls.standardize_card_name(card_data.get('name', ''))
        tcg_set = cls.standardize_set_name(
            card_data.get('set', {}).get('name', '') 
            if isinstance(card_data.get('set'), dict) else 
            card_data.get('set', '')
        )
        tcg_number = card_data.get('number', '')
        
        # Get product name from the PriceCharting result
        pc_name = cls.standardize_card_name(pricecharting_result.get('name', '') or '')
        pc_id = str(pricecharting_result.get('id', ''))
        
        # If we have empty product name but have an ID, consider it a match
        # This handles empty name responses from PriceCharting
        if not pc_name and pc_id:
            # Don't flood logs with empty name warnings
            if tcg_name:  # Only log once per batch
                logger.debug(f"Using product ID match for '{tcg_name}' with ID: {pc_id}")
            return True
            
        # Safety check for empty strings
        if not pc_name:
            return False
            
        # Extract set and number from PriceCharting product name if available
        pc_set = None
        pc_number = None
        
        # Try to extract set name from the product ID
        if pc_id:
            # Look for set codes in PC ID
            for tcg_code, pc_code in cls.SET_CODE_MAPPINGS.items():
                if pc_code and pc_code in pc_id:
                    pc_set = pc_code
                    break
        
        # Try to extract card number from the product name
        if pc_name:
            number_match = re.search(r'#(\d+)', pc_name)
            if number_match:
                pc_number = number_match.group(1)
        
        # Check if card names match (allowing for some variation)
        name_match = False
        if tcg_name in pc_name or pc_name in tcg_name:
            name_match = True
        else:
            # Check if there's a known variation
            for variations in cls.NAME_VARIATIONS.values():
                for variation in variations:
                    if variation and variation in pc_name and variation in tcg_name:
                        name_match = True
                        break
                if name_match:
                    break
        
        # Determine match confidence
        if name_match:
            if pc_number and tcg_number and pc_number == tcg_number:
                # Name and number match - high confidence
                logger.debug(f"Strong match found: '{tcg_name}' (#{tcg_number})")
                return True
            elif pc_set and tcg_set and (pc_set in tcg_set or tcg_set in pc_set):
                # Name and set match - medium confidence
                logger.debug(f"Medium match found: '{tcg_name}' (set {tcg_set})")
                return True
            else:
                # Only name matches - lower confidence
                logger.debug(f"Partial match: {tcg_name} (#{tcg_number}) with {pc_name}")
                return True
        
        # No match
        logger.debug(f"No match: {tcg_name} (#{tcg_number}) vs {pc_name}")
        return False
    
    @classmethod
    def find_best_match(cls, card_data: Dict[str, Any], products: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
        """
        Find the best matching product from a list of PriceCharting results
        
        Args:
            card_data: Card data from PokemonTCG.io API
            products: List of products from PriceCharting API
            
        Returns:
            Tuple of (best_match, confidence_score)
            Confidence scores: 3=high, 2=medium, 1=low, 0=none
        """
        if not products:
            return None, 0
            
        # Limit the number of products to check to avoid excessive processing
        products_to_check = products[:cls.MAX_PRODUCTS_TO_CHECK]
        
        best_match = None
        best_score = 0
        
        tcg_name = cls.standardize_card_name(card_data.get('name', ''))
        tcg_set = cls.standardize_set_name(
            card_data.get('set', {}).get('name', '') 
            if isinstance(card_data.get('set'), dict) else 
            card_data.get('set', '')
        )
        tcg_number = card_data.get('number', '')
        
        for product in products_to_check:
            pc_name = cls.standardize_card_name(product.get('name', '') or '')
            pc_id = str(product.get('id', ''))
            
            # Find card number in product name or ID
            pc_number = None
            number_match = re.search(r'#(\d+)', pc_name or '')
            if number_match:
                pc_number = number_match.group(1)
                
            # Extract set name from product ID if possible
            pc_set = None
            for tcg_code, pc_code in cls.SET_CODE_MAPPINGS.items():
                if pc_code and pc_id and pc_code in pc_id:
                    pc_set = pc_code
                    break
            
            # Calculate match score
            score = 0
            
            # If we have names to compare and they match
            if pc_name and tcg_name:
                if tcg_name == pc_name:
                    score += 2  # Exact name match
                elif tcg_name in pc_name or pc_name in tcg_name:
                    score += 1  # Partial name match
                
                # Check for variant matches (VMAX, EX, etc.)
                for variations in cls.NAME_VARIATIONS.values():
                    for variation in variations:
                        if variation and variation in pc_name and variation in tcg_name:
                            score += 1
                            break
            
            # If card numbers match
            if pc_number and tcg_number and pc_number == tcg_number:
                score += 1
                
            # If set names match
            if pc_set and tcg_set and (pc_set in tcg_set or tcg_set in pc_set):
                score += 1
            
            # Update best match if we found a better one
            if score > best_score:
                best_score = score
                best_match = product
                
        # Classify confidence level
        confidence = 0
        if best_score >= 4:
            confidence = 3  # High confidence
        elif best_score >= 2:
            confidence = 2  # Medium confidence
        elif best_score >= 1:
            confidence = 1  # Low confidence
                
        return best_match, confidence
    
    @classmethod
    def get_set_id_mapping(cls, tcg_set_id: str) -> Optional[str]:
        """Get the PriceCharting set identifier for a TCG set ID"""
        return cls.SET_CODE_MAPPINGS.get(tcg_set_id)
