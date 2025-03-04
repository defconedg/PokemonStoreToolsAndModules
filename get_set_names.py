import requests
import difflib  # Built-in Python module for string similarity matching

# API Keys
POKE_API_KEY = "de7a1097-afd8-4511-b9fa-6a36c18c7759"
PRICECHARTING_API_KEY = "3ada03b1de794bed535db04c27d9141af942fbd7"

# API Endpoints
POKE_API_URL = "https://api.pokemontcg.io/v2/sets"
PRICECHARTING_API_URL = f"https://www.pricecharting.com/api/products?t={PRICECHARTING_API_KEY}&q=pokemon"

# Function to get all sets from PokémonTCG.io API
def get_pokemon_tcg_sets():
    headers = {"X-Api-Key": POKE_API_KEY}
    response = requests.get(POKE_API_URL, headers=headers)

    if response.status_code != 200:
        print("❌ Error fetching PokémonTCG.io sets!")
        return {}

    sets = response.json().get("data", [])
    tcg_sets = {s["id"]: s["name"] for s in sets}

    # Print raw list for manual mapping
    print("\n📜 RAW PokémonTCG.io Sets (Manual Mapping):")
    for set_id, set_name in tcg_sets.items():
        print(f"{set_id} | {set_name}")

    return tcg_sets

# Function to get Pokémon set names from PriceCharting API
def get_pricecharting_sets():
    response = requests.get(PRICECHARTING_API_URL)

    if response.status_code != 200:
        print("❌ Error fetching PriceCharting sets!")
        return []

    products = response.json().get("products", [])
    pricecharting_sets = sorted(set(product["console-name"] for product in products))

    # Print raw list for manual mapping
    print("\n📜 RAW PriceCharting Sets (Manual Mapping):")
    for set_name in pricecharting_sets:
        print(set_name)

    return pricecharting_sets

# Function to map PokémonTCG.io sets to PriceCharting sets using difflib
def create_conversion_dict(tcgo_sets, pricecharting_sets):
    conversion_dict = {}

    print("\n🔄 Auto-Matching PokémonTCG.io Sets to PriceCharting Sets...")

    for tcg_set_id, tcg_set_name in tcgo_sets.items():
        best_match = difflib.get_close_matches(tcg_set_name, pricecharting_sets, n=1, cutoff=0.8)  # 80% match threshold
        if best_match:
            conversion_dict[tcg_set_id] = {
                "PokemonTCG.io Name": tcg_set_name,
                "PriceCharting Name": best_match[0]
            }
            print(f"✅ Matched: {tcg_set_name} → {best_match[0]}")
        else:
            print(f"❌ No strong match for: {tcg_set_name}")

    return conversion_dict

# Main Execution
pokemon_tcg_sets = get_pokemon_tcg_sets()
pricecharting_sets = get_pricecharting_sets()

# Generate conversion dictionary
conversion_dict = create_conversion_dict(pokemon_tcg_sets, pricecharting_sets)

# Print the final mapping
print("\n🎯 FINAL CONVERSION DICTIONARY (Auto-Matches):")
for key, value in conversion_dict.items():
    print(f"{key}: {value}")

