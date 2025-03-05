"""
Direct matching module for problematic Pokemon cards that need special handling
Uses the working approach from card_diagnostic.py
"""
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DirectMatcher:
    """
    Handles direct matching for problematic cards that don't work with standard lookup
    """
    
    @staticmethod
    def match_hgss_triumphant_ditto(api_key: Optional[str] = None) -> Dict[str, Any]:
        """Special matcher for Ditto from HS-Triumphant"""
        logger.info("Using special direct matcher for Ditto (HS-Triumphant)")
        
        # Direct API call to PriceCharting using the exact approach from card_diagnostic.py
        url = "https://www.pricecharting.com/api/product"
        params = {
            "t": api_key,
            "q": "pokemon Ditto HS Triumphant 17"  # Exact query that works
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                # Format prices to our standard format
                return {
                    'loose': float(data.get("loose-price", 0)) / 100.0,
                    'graded': float(data.get("graded-price", 0)) / 100.0,
                    'psa_grades': {
                        'psa-10': float(data.get("manual-only-price", 0)) / 100.0,
                        'psa-9': float(data.get("graded-price", 0)) / 100.0,
                        'psa-8': float(data.get("new-price", 0)) / 100.0,
                    },
                    '_product_id': data.get("id", ""),
                    '_product_name': data.get("product-name", "Ditto (HS-Triumphant)"),
                    '_match_confidence': 3  # High confidence for direct match
                }
            else:
                logger.warning("Direct match API call failed for HS-Triumphant Ditto")
                return {}
        except Exception as e:
            logger.error(f"Error in direct matcher for HS-Triumphant Ditto: {str(e)}")
            return {}
    
    @staticmethod
    def get_special_match(card_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Get special matching for known problematic cards"""
        if card_id == "hgss4-17":  # Ditto from HS-Triumphant
            return DirectMatcher.match_hgss_triumphant_ditto(api_key)
        # Add more special cases as needed
        return {}
