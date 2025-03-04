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

Set your API keys in `config.py` or use environment variables: