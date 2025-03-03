"""
Configuration file for API keys
"""

POKEMON_TCG_API_KEY = "de7a1097-afd8-4511-b9fa-6a36c18c7759"
PRICE_CHARTING_API_TOKEN = "3ada03b1de794bed535db04c27d9141af942fbd7"

# API Base URLs
# ===============================

# Price Charting API base URL
PRICE_CHARTING_BASE_URL = "https://www.pricecharting.com"

# Pokemon TCG API base URL
POKEMON_TCG_BASE_URL = "https://api.pokemontcg.io/v2"

# PokeAPI base URL (no authentication required)
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

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
SET_MAPPINGS = {
    "Twilight Masquerade": {"tcg_id": "sv5", "pc_id": "65957"},
    "Temporal Forces": {"tcg_id": "sv4", "pc_id": "65269"},
    "Paradox Rift": {"tcg_id": "sv3", "pc_id": "63241"},
    "Scarlet & Violet": {"tcg_id": "sv1", "pc_id": "57223"},
    "Paldea Evolved": {"tcg_id": "sv2", "pc_id": "58963"},
    "Crown Zenith": {"tcg_id": "swsh12pt5", "pc_id": "56688"},
    "Silver Tempest": {"tcg_id": "swsh12", "pc_id": "54662"},
    "Lost Origin": {"tcg_id": "swsh11", "pc_id": "54087"},
    "Astral Radiance": {"tcg_id": "swsh10", "pc_id": "53062"},
    "Brilliant Stars": {"tcg_id": "swsh9", "pc_id": "52455"},
    "Fusion Strike": {"tcg_id": "swsh8", "pc_id": "51414"},
    "Evolving Skies": {"tcg_id": "swsh7", "pc_id": "50472"},
    "Chilling Reign": {"tcg_id": "swsh6", "pc_id": "49525"},
    "Battle Styles": {"tcg_id": "swsh5", "pc_id": "48581"},
    # Add direct entry for Pokemon 151 set
    "Pokemon 151": {"tcg_id": "sv3pt5", "pc_id": "63941"},
    # Add alternative name for finding it
    "151": {"tcg_id": "sv3pt5", "pc_id": "63941"}
}

