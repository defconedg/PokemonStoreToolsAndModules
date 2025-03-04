# Pokemon Store Tools and Modules

A collection of Python modules and tools for working with Pokemon card data, pricing, and game information from multiple API sources.

## Overview

This repository contains a set of Python modules for accessing and combining data from multiple Pokemon-related APIs:
- **Pokemon TCG API** (pokemontcg.io) - For card data, images and pricing
- **Price Charting API** (pricecharting.com) - For video game and collectible pricing
- Combined tools for store management, price comparison and data retrieval

## Modules

### PokemonTCG Client
A comprehensive client for the Pokemon TCG API with support for:
- Searching cards by various parameters
- Finding information about sets
- Retrieving card images and pricing data
- Support for all endpoints (types, subtypes, supertypes, rarities)

### Price Charting Client
A wrapper for the Price Charting API that provides:
- Product lookup by ID, UPC, or name
- Pricing information for games and collectibles
- Image retrieval and downloading
- Support for marketplace offers

### Pokemon Price Helper
A combined tool that brings together functionality from both APIs for:
- Cross-referencing pricing data between sources
- Searching for cards and games
- Tracking collection values
- Retrieving and comparing images

## Configuration

Set your API keys in `config.py` or use environment variables.

## Installation & Usage

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the arbitrage tool: `python app.py`
4. Access the web interface at http://localhost:5000

## API Keys

To use this application, you'll need:

1. Pokemon TCG API key (get one at https://dev.pokemontcg.io/)
2. PriceCharting API key (optional)

## Error Handling

The application includes robust error handling:
- Automatic retry with exponential backoff for API rate limits
- Graceful fallback to cached data when APIs are unavailable
- Detailed logging for troubleshooting

## Caching System

To minimize API calls and improve performance, the application implements a caching system:
- Card data cached for 12 hours
- Set data cached for 1 week
- Search results cached for 3 days
- Automatic cache invalidation for stale data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.