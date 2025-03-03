"""
PriceCharting API wrapper
"""

import requests
import os
from typing import Dict, Any, List, Optional
from config import PRICE_CHARTING_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES
from bs4 import BeautifulSoup  # Add this import for HTML parsing

class PriceCharting:
    """
    API wrapper for PriceCharting.com
    """
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = PRICE_CHARTING_BASE_URL
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES
        
        # Validate API token
        if not self.api_token:
            print("WARNING: PriceCharting API token is empty. API calls will fail.")

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an authenticated request to the PriceCharting API
        """
        if params is None:
            params = {}
            
        # Always include the API token in the parameters WITH THE CORRECT PARAMETER NAME 't'
        params['t'] = self.api_token
        
        url = f"{self.base_url}{endpoint}"
        
        retries = 0
        while retries <= self.max_retries:
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries > self.max_retries:
                    raise Exception(f"Failed to make request after {self.max_retries} attempts: {str(e)}")
                print(f"Request failed, retrying ({retries}/{self.max_retries})...")
    
    def cents_to_dollars(self, cents: int) -> float:
        """
        Convert cents to dollars
        """
        return cents / 100.0 if cents else 0.0
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """
        Get product information by ID
        """
        return self._make_request("/api/product", {"id": product_id})
    
    def get_product_by_upc(self, upc: str) -> Dict[str, Any]:
        """
        Get product information by UPC
        """
        return self._make_request("/api/product", {"upc": upc})
    
    def get_product_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get best match product by name
        Uses full text search to find the best match
        """
        return self._make_request("/api/product", {"q": name})
    
    def search_products(self, query: str) -> Dict[str, Any]:
        """
        Search for products by name
        """
        return self._make_request("/api/products", {"q": query})
    
    def search_by_console(self, console: str, query: str = None) -> Dict[str, Any]:
        """
        Search for products by console name, with optional query
        """
        params = {"console": console}
        if query:
            params["q"] = query
        return self._make_request("/api/products", params)
    
    def get_offers_by_status(self, status: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get marketplace offers by status (available, sold, etc.)
        """
        params = {"status": status}
        if filters:
            params.update(filters)
        return self._make_request("/api/offers", params)
    
    def get_offer_details(self, offer_id: str) -> Dict[str, Any]:
        """
        Get details for a specific marketplace offer
        """
        return self._make_request("/api/offer-details", {"offer-id": offer_id})
    
    def get_product_image_url(self, product_id: str, product_name: str = "", console_name: str = "") -> str:
        """
        Get the image URL for a product by scraping the product page
        
        Args:
            product_id: The product ID
            product_name: The product name (optional, helps with URL construction)
            console_name: The console name (optional, helps with URL construction)
            
        Returns:
            The URL to the product image or None if not found
        """
        try:
            # First try to get the product page URL
            if product_name and console_name:
                # Convert names to URL-friendly format
                console_slug = console_name.lower().replace(" ", "-")
                product_slug = product_name.lower().replace(" ", "-").replace(":", "").replace("'", "")
                product_page_url = f"{self.base_url}/game/{console_slug}/{product_slug}"
            else:
                # Fallback to generic URL with ID
                product_page_url = f"{self.base_url}/game/{product_id}"
            
            # Request the product page
            response = requests.get(product_page_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse the HTML to find the image URL
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the main product image
            img_tag = soup.select_one('img.product')
            if img_tag and img_tag.has_attr('src'):
                img_url = img_tag['src']
                # Make sure it's an absolute URL
                if img_url.startswith('/'):
                    img_url = f"{self.base_url}{img_url}"
                return img_url
            
            # Alternative selector if the first one doesn't work
            img_tag = soup.select_one('.product-image img')
            if img_tag and img_tag.has_attr('src'):
                img_url = img_tag['src']
                # Make sure it's an absolute URL
                if img_url.startswith('/'):
                    img_url = f"{self.base_url}{img_url}"
                return img_url
                
            print(f"Warning: Couldn't find image on product page {product_page_url}")
            return None
        except Exception as e:
            print(f"Error getting image URL for product {product_id}: {str(e)}")
            return None
    
    def download_product_image(self, product_id: str, product_name: str = None, console_name: str = None) -> str:
        """
        Download the product image to a local folder
        
        Args:
            product_id: The product ID
            product_name: Optional name for the file (defaults to product_id)
            console_name: Optional console name to help construct the URL
            
        Returns:
            The local file path to the downloaded image or None if download failed
        """
        # Create images directory if it doesn't exist
        image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        # Use product name if provided, otherwise use product ID
        file_name = f"{product_name.replace(' ', '_')}_{product_id}.jpg" if product_name else f"{product_id}.jpg"
        local_path = os.path.join(image_dir, file_name)
        
        # Get the image URL
        image_url = self.get_product_image_url(product_id, product_name, console_name)
        
        if not image_url:
            print(f"Could not find image URL for product {product_id}")
            return None
        
        try:
            # Download the image
            response = requests.get(image_url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            # Check if the response content is an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                print(f"Warning: Response from {image_url} is not an image. Content-Type: {content_type}")
                return None
            
            # Save the image to the local file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Successfully downloaded image to {local_path}")
            return local_path
        except requests.exceptions.RequestException as e:
            print(f"Error downloading image for product {product_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error downloading image for product {product_id}: {str(e)}")
            return None
    
    def get_complete_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Get complete product details including all available pricing fields
        """
        product_data = self.get_product_by_id(product_id)
        
        # Process the raw data to create a more friendly response format
        details = {
            "id": product_id,
            "product_name": product_data.get("product-name", ""),
            "console_name": product_data.get("console-name", ""),
            "release_date": product_data.get("release-date", ""),
            "upc": product_data.get("upc", ""),
            "asin": product_data.get("asin", ""),
            "epid": product_data.get("epid", ""),
            "genre": product_data.get("genre", ""),
            "sales_volume": product_data.get("sales-volume", ""),
            
            # All available pricing points
            "prices": {
                "loose": self.cents_to_dollars(product_data.get("loose-price", 0)),
                "cib": self.cents_to_dollars(product_data.get("cib-price", 0)),
                "new": self.cents_to_dollars(product_data.get("new-price", 0)),
            }
        }
        
        # Add optional pricing fields if they exist
        optional_price_mappings = {
            "graded-price": "graded",
            "box-only-price": "box_only",
            "manual-only-price": "manual_only",
            "bgs-10-price": "bgs_10",
            "condition-17-price": "cgc_10",  # Cards: CGC 10
            "condition-18-price": "sgc_10",  # Cards: SGC 10
            "gamestop-price": "gamestop",
            "retail-loose-buy": "retail_loose_buy",
            "retail-loose-sell": "retail_loose_sell",
            "retail-cib-buy": "retail_cib_buy",
            "retail-cib-sell": "retail_cib_sell",
            "retail-new-buy": "retail_new_buy",
            "retail-new-sell": "retail_new_sell"
        }
        
        # Add each optional price field if it exists in the product data
        for api_key, details_key in optional_price_mappings.items():
            if api_key in product_data and product_data[api_key]:
                details["prices"][details_key] = self.cents_to_dollars(product_data[api_key])
        
        return details