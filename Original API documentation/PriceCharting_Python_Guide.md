# PriceCharting API Python Guide

This guide provides instructions for using the Python PriceCharting API wrapper. This wrapper makes it easy to interact with PriceCharting's API to get pricing data for video games, trading cards, and other collectibles.

## Table of Contents

- [Setup](#setup)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Marketplace Operations](#marketplace-operations)
- [API Reference](#api-reference)
- [Common Use Cases](#common-use-cases)

## Setup

1. Make sure you have the `requests` library installed:

```bash
pip install requests
```

2. Import the PriceCharting client:

```python
from price_charting import PriceCharting
```

3. Initialize the client:

```python
price_charting = PriceCharting("your-api-token")
```

## Basic Usage

### Looking up a single product

```python
# By ID
product = price_charting.get_product_by_id("6910")
print(product)

# By UPC
product = price_charting.get_product_by_upc("045496830434")
print(product)

# By name search
product = price_charting.get_product_by_name("Pokémon Red GameBoy")
print(product)
```

### Searching for products

```python
results = price_charting.search_products("Zelda Nintendo 64")
print(f"Found {len(results.get('products', []))} products:")
for product in results.get('products', []):
    print(f"- {product['product-name']} ({product['console-name']}): ID {product['id']}")
```

### Getting complete price information

```python
price_data = price_charting.get_prices("6910")
print(f"Product: {price_data['product_name']}")
print(f"Loose price: ${price_data['prices'].get('loose-price', {}).get('dollars')}")
print(f"Complete in Box price: ${price_data['prices'].get('cib-price', {}).get('dollars')}")
print(f"New/Sealed price: ${price_data['prices'].get('new-price', {}).get('dollars')}")
```

## Advanced Features

### Getting all product details

```python
details = price_charting.get_complete_product_details("6910")
import json
print('Complete Product Details:')
print(json.dumps(details, indent=2))
```

### Searching by console

```python
results = price_charting.search_by_console("nintendo 64", "mario")
print("Mario games for Nintendo 64:")
for product in results.get('products', []):
    print(f"- {product['product-name']}")
```

### Getting product image URL

```python
image_url = price_charting.get_product_image_url("6910")
print(f"Image URL: {image_url}")
```

## Marketplace Operations

### Getting marketplace offers

```python
offers = price_charting.get_offers_by_status("available", {"console": "G13"})
print("Available Super Nintendo offers:")
for offer in offers.get('offers', []):
    print(f"{offer['product-name']} - ${offer['price'] / 100} - {offer['condition-string']}")
```

### Publishing a new offer

```python
offer_data = {
    "product": "9331",
    "condition-id": 1,
    "price-max": 901,
    "sku": "METNES001"
}

result = price_charting.publish_offer(offer_data)
print(f"New offer published: {result['offer-id']}")
print(f"Price: ${result['price'] / 100}")
```

### Getting offer details

```python
details = price_charting.get_offer_details("smzksacsy5i2dsrddxsrlzsp6i")
print(f"Offer details for {details['product-name']}")
if details.get('is-sold'):
    print(f"Sold for: ${details['price'] / 100}")
    print(f"Buyer: {details['buyer']['shipping-name']}")
```

### Managing your listings

```python
# Mark an offer as shipped
result = price_charting.mark_as_shipped("smzksacsy5i2dsrddxsrlzsp6i", "9400111234567890000000")
print(f"Offer marked as shipped: {result}")

# End an offer
result = price_charting.end_offer("vtdsww72uyslgooawzyyijsllm")
print(f"Offer ended: {result}")

# Submit feedback
result = price_charting.submit_feedback("smzksacsy5i2dsrddxsrlzsp6i", 2, "Great buyer, fast payment!")
print(f"Feedback submitted: {result}")
```

## API Reference

### Main Methods

| Method | Purpose |
|--------|---------|
| `get_product_by_id` | Get a single product by its PriceCharting ID |
| `get_product_by_upc` | Get a single product by its UPC code |
| `get_product_by_name` | Search for a product by name (returns best match) |
| `search_products` | Search for multiple products (returns list) |
| `get_prices` | Get detailed pricing for a specific product |
| `get_complete_product_details` | Get all available information about a product |
| `get_offers` | Get marketplace listings based on criteria |
| `publish_offer` | Create a new marketplace listing |
| `get_offer_details` | Get detailed information about an offer |
| `search_by_console` | Search for products by console name |

### Price Data Fields

The price data includes multiple formats:

- `loose-price`: Item only, no packaging or manuals
- `cib-price`: Complete in box (item, original box, manual)
- `new-price`: New/sealed item
- `graded-price`: Professionally graded item
- `box-only-price`: Original box only
- `manual-only-price`: Manual only
- `bgs-10-price`: Cards: BGS 10 / Comics: Graded 10.0
- `condition-17-price`: Cards: CGC 10 / Comics: Graded 9.4
- `condition-18-price`: Cards: SGC 10

### Console IDs

The wrapper includes a helper method `get_console_id_by_name()` that maps common console names to their PriceCharting IDs. Some examples:

- "nintendo 64" → "G4"
- "playstation" → "G6"
- "gameboy" → "G49"
- "snes" → "G13"
- "xbox" → "G8"
- "pokemon cards" → "G56"

## Common Use Cases

### Building a Price Comparison Tool

```python
def compare_product_prices(product_names):
    results = []
    
    for name in product_names:
        try:
            product = price_charting.get_product_by_name(name)
            if product["status"] == "success":
                results.append({
                    "name": product["product-name"],
                    "console": product["console-name"],
                    "loose_price": price_charting.cents_to_dollars(product.get("loose-price")),
                    "cib_price": price_charting.cents_to_dollars(product.get("cib-price")),
                    "new_price": price_charting.cents_to_dollars(product.get("new-price"))
                })
        except Exception as e:
            print(f"Error fetching {name}: {str(e)}")
    
    return results

# Example usage
games_to_compare = ["Pokémon Red", "Zelda Ocarina of Time", "Super Mario 64"]
comparison = compare_product_prices(games_to_compare)
for game in comparison:
    print(f"{game['name']} ({game['console']})")
    print(f"  Loose: ${game['loose_price']}")
    print(f"  CIB: ${game['cib_price']}")
    print(f"  New: ${game['new_price']}")
```

### Collection Value Tracking

```python
def track_collection_value(product_ids):
    total_value = 0
    items = []
    
    for product_id in product_ids:
        try:
            details = price_charting.get_complete_product_details(product_id)
            if details["status"] == "success":
                loose_value = details["prices"]["loose"] or 0
                total_value += loose_value
                items.append({
                    "name": details["product_name"],
                    "value": loose_value
                })
        except Exception as e:
            print(f"Error with product {product_id}: {str(e)}")
    
    return {
        "items": items,
        "total_value": total_value
    }

# Example usage
collection_ids = ["6910", "4801", "2611"]  # EarthBound, Tactics Ogre PS1, Tactics Ogre GBA
collection = track_collection_value(collection_ids)
print(f"Total collection value: ${collection['total_value']:.2f}")
for item in collection["items"]:
    print(f"- {item['name']}: ${item['value']:.2f}")
```

### Finding the Best Marketplace Deals

```python
def find_best_deals(product_name, condition="loose"):
    # Map condition to condition ID
    condition_map = {"loose": 1, "cib": 2, "new": 3}
    condition_id = condition_map.get(condition.lower(), 1)
    
    # Search for the product
    product_search = price_charting.search_products(product_name)
    if product_search["status"] != "success" or not product_search.get("products"):
        return {"status": "error", "message": "No products found"}
    
    # Get the first product
    product_id = product_search["products"][0]["id"]
    product_name = product_search["products"][0]["product-name"]
    
    # Get official price
    product_details = price_charting.get_complete_product_details(product_id)
    official_price = None
    if condition == "loose":
        official_price = product_details["prices"]["loose"]
    elif condition == "cib":
        official_price = product_details["prices"]["cib"]
    elif condition == "new":
        official_price = product_details["prices"]["new"]
    
    # Get marketplace offers
    offers = price_charting.get_offers_for_product(product_id)
    
    # Filter by condition
    filtered_offers = [
        offer for offer in offers.get("offers", [])
        if offer["condition-id"] == condition_id
    ]
    
    # Sort by price
    sorted_offers = sorted(filtered_offers, key=lambda x: x["price"])
    
    return {
        "product_name": product_name,
        "official_price": official_price,
        "offers": [
            {
                "price": price_charting.cents_to_dollars(offer["price"]),
                "condition": offer["condition-string"],
                "url": f"{price_charting.base_url}{offer['offer-url']}"
            }
            for offer in sorted_offers[:5]  # Top 5 offers
        ]
    }

# Example usage
deals = find_best_deals("Pokémon Red", "loose")
print(f"Best deals for {deals['product_name']}:")
print(f"Official price: ${deals['official_price']:.2f}")
print("Marketplace offers:")
for i, offer in enumerate(deals["offers"], 1):
    print(f"{i}. ${offer['price']:.2f} - {offer['condition']}")
    print(f"   URL: {offer['url']}")
```

---

**Note**: Remember to handle API rate limits appropriately and implement error handling in your production code.

For more information, refer to [PriceCharting API Documentation](https://www.pricecharting.com/page/api) (requires PriceCharting subscription).
