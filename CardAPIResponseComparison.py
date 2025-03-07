import requests
import json
import urllib.parse
import re
from colorama import init, Fore, Style

# Initialize colorama for Windows terminal color support
init(autoreset=True)

# API Keys (copied from the original script)
POKE_API_KEY = "de7a1097-afd8-4511-b9fa-6a36c18c7759"
PRICECHARTING_API_KEY = "3ada03b1de794bed535db04c27d9141af942fbd7"

def query_tcg_card(set_id, card_number):
    """Query the Pokemon TCG API by set id and card number."""
    query = f'set.id:"{set_id}" AND number:"{card_number}"'
    url = f"https://api.pokemontcg.io/v2/cards?q={urllib.parse.quote(query)}"
    
    print(Fore.YELLOW + f"Making request to: {url}")
    
    response = requests.get(url, headers={"X-Api-Key": POKE_API_KEY})
    if response.status_code != 200:
        print(Fore.RED + f"Error: API returned status code {response.status_code}")
        return None
    
    data = response.json()
    return data

def normalize_number(n):
    """Convert card numbers like '05', '5', or '005' into a standard string (e.g. '5')."""
    if n is None:
        return None
    try:
        return str(int(n))
    except:
        return n

def determine_printing(card):
    """Determine printing from variant flags, falling back to rarity."""
    variants = card.get("variants", {})
    if variants.get("reverseHolo"):
        return "Reverse Holo"
    if variants.get("holo"):
        return "Holo"
    rarity = card.get("rarity", "").lower()
    if "reverse holo" in rarity:
        return "Reverse Holo"
    if any(x in rarity for x in ["holo", "illustration", "promo"]):
        return "Holo"
    return "Normal"

def get_expected_printing(card, user_printing=None):
    """Return expected printing, checking for holofoil prices if needed or using user input."""
    if user_printing:
        return user_printing
        
    printing = determine_printing(card)
    prices = card.get("tcgplayer", {}).get("prices", {})
    if printing == "Normal" and "holofoil" in prices:
        printing = "Holo"
    return printing

def build_pc_query(card, include_printing=True, user_printing=None):
    """Build a PriceCharting query string from TCG card data."""
    name = card.get("name", "Unknown")
    number = normalize_number(card.get("number", "Unknown"))
    set_name = card.get("set", {}).get("name", "Unknown")
    
    # Use user-specified printing if provided, otherwise determine from card
    expected = get_expected_printing(card, user_printing)
    
    # Format the set name consistently for PriceCharting
    pc_set = "Pokemon " + set_name
    
    # Build query with more consistent formatting for better matching
    if include_printing and expected.lower() != "normal":
        return f"{pc_set} {name} [{expected}] #{number}"
    return f"{pc_set} {name} #{number}"

def query_pc(query):
    """Query the PriceCharting API with the given search query."""
    url = "https://www.pricecharting.com/api/products"
    params = {"t": PRICECHARTING_API_KEY, "q": query}
    
    print(Fore.YELLOW + f"Making request to: {url} with query: {query}")
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(Fore.RED + f"Error: API returned status code {response.status_code}")
        return None
    
    data = response.json()
    return data

def find_matching_card(pc_data, card_name, card_number, printing_type):
    """Find the best matching card in PriceCharting results."""
    if not pc_data or not pc_data.get("products"):
        return None
    
    products = pc_data["products"]
    matches = []
    
    for product in products:
        product_name = product.get("product-name", "")
        
        # Check if the card number matches
        number_match = False
        number_pattern = r"#(\d+)"
        number_search = re.search(number_pattern, product_name)
        if number_search and normalize_number(number_search.group(1)) == normalize_number(card_number):
            number_match = True
        
        # Check for printing type
        printing_match = False
        if printing_type.lower() == "normal":
            # For normal cards, they shouldn't have [Holo] or [Reverse Holo] in name
            if not re.search(r"\[(Reverse )?Holo\]", product_name):
                printing_match = True
        else:
            # For special printings, we should find the type in brackets
            if f"[{printing_type}]" in product_name:
                printing_match = True
        
        # If we have matches on both number and printing, add to potential matches
        if number_match and printing_match:
            matches.append(product)
    
    # Return the best match - for now, just the first one
    return matches[0] if matches else None

def get_sets():
    """Get all available Pokemon TCG sets."""
    url = "https://api.pokemontcg.io/v2/sets"
    response = requests.get(url, headers={"X-Api-Key": POKE_API_KEY})
    if response.status_code != 200:
        print(Fore.RED + f"Error: API returned status code {response.status_code}")
        return []
    
    return response.json().get("data", [])

def display_sets(sets):
    """Display a list of available sets."""
    print(Fore.CYAN + "\nAvailable Sets:")
    print("-" * 80)
    print(f"{'Set ID':<15} {'Set Name':<40} {'Total Cards':<12}")
    print("-" * 80)
    
    for set_data in sets:
        set_id = set_data.get("id", "Unknown")
        set_name = set_data.get("name", "Unknown")
        total = set_data.get("printedTotal") or set_data.get("total") or "Unknown"
        print(f"{set_id:<15} {set_name:<40} {total:<12}")

def display_price_comparison(tcg_card, pc_product):
    """Display price comparison between TCGplayer and PriceCharting."""
    print(Fore.CYAN + "\n" + "=" * 80)
    print(Fore.CYAN + "PRICE COMPARISON".center(80))
    print(Fore.CYAN + "=" * 80)
    
    # TCGplayer prices
    tcg_prices = tcg_card.get("tcgplayer", {}).get("prices", {})
    printing_types = list(tcg_prices.keys())
    tcg_market_price = None
    
    if printing_types:
        main_printing = printing_types[0]  # e.g., 'holofoil', 'normal', etc.
        tcg_market_price = tcg_prices[main_printing].get("market")
        
        print(Fore.GREEN + "\nTCGplayer Prices:")
        print("-" * 40)
        print(f"Market Price: ${tcg_market_price:.2f}")
        print(f"Low: ${tcg_prices[main_printing].get('low', 0):.2f}")
        print(f"Mid: ${tcg_prices[main_printing].get('mid', 0):.2f}")
        print(f"High: ${tcg_prices[main_printing].get('high', 0):.2f}")
    
    # CardMarket prices (EU)
    cardmarket = tcg_card.get("cardmarket", {}).get("prices", {})
    cm_trend_price = cardmarket.get("trendPrice")
    
    if cm_trend_price is not None:
        print(Fore.BLUE + "\nCardMarket Prices (EU):")
        print("-" * 40)
        print(f"Trend Price: €{cm_trend_price:.2f}")
        print(f"Average Sell Price: €{cardmarket.get('averageSellPrice', 0):.2f}")
        print(f"Low Price: €{cardmarket.get('lowPrice', 0):.2f}")
    
    # PriceCharting prices
    if pc_product:
        pc_loose_price = pc_product.get("loose-price", 0) / 100  # Convert cents to dollars
        
        print(Fore.MAGENTA + "\nPriceCharting Prices:")
        print("-" * 40)
        print(f"Loose Price: ${pc_loose_price:.2f}")
        if pc_product.get("new-price"):
            print(f"New Price: ${pc_product.get('new-price', 0) / 100:.2f}")
        
        # Add arbitrage comparison
        if tcg_market_price and pc_loose_price > 0:
            diff = tcg_market_price - pc_loose_price
            pct_diff = (diff / pc_loose_price) * 100
            
            print(Fore.YELLOW + "\nArbitrage Analysis:")
            print("-" * 40)
            if diff > 0:
                print(f"TCGplayer is ${diff:.2f} ({abs(pct_diff):.1f}%) MORE expensive than PriceCharting")
            else:
                print(f"TCGplayer is ${abs(diff):.2f} ({abs(pct_diff):.1f}%) LESS expensive than PriceCharting")
                
            if abs(pct_diff) > 15:
                print(Fore.RED + "POTENTIAL ARBITRAGE OPPORTUNITY DETECTED!")

def main():
    print(Fore.GREEN + "=" * 80)
    print(Fore.GREEN + "Pokemon Card API Response Comparison Tool".center(80))
    print(Fore.GREEN + "=" * 80)
    
    # Get all available sets
    print(Fore.YELLOW + "\nFetching available Pokemon TCG sets...")
    sets = get_sets()
    
    if not sets:
        print(Fore.RED + "Failed to retrieve sets. Exiting.")
        return
    
    # Display search options
    while True:
        print(Fore.CYAN + "\nSearch Options:")
        print("1. List all available sets")
        print("2. Search by set ID and card number")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            display_sets(sets)
            
        elif choice == '2':
            set_id = input("\nEnter set ID (e.g., swsh1, sv1): ")
            card_number = input("Enter card number: ")
            printing_options = ["Normal", "Holo", "Reverse Holo"]
            
            print("\nSelect printing type:")
            for i, p_type in enumerate(printing_options, 1):
                print(f"{i}. {p_type}")
            
            printing_choice = input("Enter choice (or press Enter for auto-detect): ")
            user_printing = None
            if printing_choice.isdigit() and 1 <= int(printing_choice) <= len(printing_options):
                user_printing = printing_options[int(printing_choice) - 1]
            
            # Query Pokemon TCG API
            print(Fore.YELLOW + "\nQuerying Pokemon TCG API...")
            tcg_data = query_tcg_card(set_id, card_number)
            
            if not tcg_data or not tcg_data.get("data"):
                print(Fore.RED + "Failed to retrieve TCG data or no cards found.")
                continue
                
            # Get the first card from the response
            card = tcg_data.get("data", [])[0]
            
            # Display the full TCG API response
            print(Fore.GREEN + "\nPokemon TCG API Full Response:")
            print("=" * 80)
            print(json.dumps(card, indent=2))
            
            # Generate PriceCharting query with user's printing type if specified
            pc_query = build_pc_query(card, include_printing=True, user_printing=user_printing)
            
            # Query PriceCharting API
            print(Fore.YELLOW + "\nQuerying PriceCharting API...")
            pc_data = query_pc(pc_query)
            
            matching_product = None
            if pc_data and pc_data.get("products"):
                # Try to find the exact matching card
                printing_type = user_printing if user_printing else get_expected_printing(card)
                matching_product = find_matching_card(pc_data, card.get("name"), card.get("number"), printing_type)
                
                # Display the full PriceCharting API response
                print(Fore.GREEN + "\nPriceCharting API Results:")
                print("=" * 80)
                print(json.dumps(pc_data, indent=2))
                
                if matching_product:
                    print(Fore.GREEN + "\nFound matching card in PriceCharting:")
                    print(json.dumps(matching_product, indent=2))
                else:
                    print(Fore.YELLOW + "\nNo exact match found. Trying without printing specification...")
                    # Try without printing specification
                    pc_query = build_pc_query(card, include_printing=False)
                    pc_data = query_pc(pc_query)
                    
                    if pc_data and pc_data.get("products"):
                        print(Fore.GREEN + "\nPriceCharting API Results (without printing):")
                        print("=" * 80)
                        print(json.dumps(pc_data, indent=2))
                        
                        # Now try to find the best match
                        matching_product = find_matching_card(pc_data, card.get("name"), card.get("number"), "Normal")
                        
                        if matching_product:
                            print(Fore.GREEN + "\nFound potential matching card:")
                            print(json.dumps(matching_product, indent=2))
            
            # Compare prices and show arbitrage opportunities
            if matching_product:
                display_price_comparison(card, matching_product)
            else:
                print(Fore.RED + "\nCould not find matching card on PriceCharting for price comparison.")
                
        elif choice == '3':
            print(Fore.GREEN + "\nExiting. Thank you for using the API Comparison Tool!")
            break
            
        else:
            print(Fore.RED + "Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
