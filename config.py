"""
Configuration settings for the Pokémon Card Arbitrage Tool
"""
import os

# API Keys - Use environment variables instead of hardcoded values
POKEMON_TCG_API_KEY = os.environ.get('POKEMON_TCG_API_KEY', '')
PRICE_CHARTING_API_TOKEN = os.environ.get('PRICE_CHARTING_API_KEY', '')

# API Base URLs
# ===============================

# Price Charting API base URL
PRICE_CHARTING_BASE_URL = "https://www.pricecharting.com"

# Pokemon TCG API base URL
POKEMON_TCG_BASE_URL = "https://api.pokemontcg.io/v2"

# PokeAPI base URL (no authentication required)
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

# Currency Conversion Rates
# ===============================

# EUR to USD conversion rate (for converting CardMarket prices to USD)
EUR_TO_USD_CONVERSION_RATE = 1.09  # Example rate, adjust as needed

# USD to EUR conversion rate (for converting US prices to CardMarket)
USD_TO_EUR_CONVERSION_RATE = 0.92  # Example rate, adjust as needed

# Marketplace fees (percentage as decimal)
FEES = {
    'tcgplayer': 0.15,  # 15% fee (includes platform fee + payment processing)
    'cardmarket': 0.05,  # 5% fee
    'pricecharting': 0.13  # 13% fee (estimated average)
}

# Shipping costs (in USD)
SHIPPING = {
    'domestic': 1.00,
    'international': 5.00
}

# Supported grading companies
GRADING_COMPANIES = ['PSA', 'BGS', 'CGC']

# Card conditions
CARD_CONDITIONS = [
    'Poor', 'Fair', 'Good', 'Very Good', 'Excellent', 'Near Mint', 'Mint', 'Gem Mint'
]

# Optional configuration settings
# ===============================

# Maximum number of retries for API requests
MAX_RETRIES = 3

# Timeout for API requests (in seconds)
REQUEST_TIMEOUT = 15

# Test Mode (set to True to enable test mode)
# ===============================
TEST_MODE = False

# Known set mappings - helps with accurate data matching
# ===============================
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
}


