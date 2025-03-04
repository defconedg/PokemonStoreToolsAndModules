"""
Utility functions for working with Pokemon card set mappings
"""
from config import SET_MAPPING

def get_pricecharting_name(tcg_set_code):
    """
    Get the PriceCharting set name for a given TCG.io set code
    
    Args:
        tcg_set_code (str): The set code from PokemonTCG.io API
        
    Returns:
        str: The corresponding PriceCharting set name, or None if not found
    """
    set_info = SET_MAPPING.get(tcg_set_code)
    if set_info:
        return set_info.get("pricecharting_name")
    return None

def get_tcg_name(tcg_set_code):
    """
    Get the TCG.io set name for a given TCG.io set code
    
    Args:
        tcg_set_code (str): The set code from PokemonTCG.io API
        
    Returns:
        str: The corresponding TCG.io set name, or None if not found
    """
    set_info = SET_MAPPING.get(tcg_set_code)
    if set_info:
        return set_info.get("tcg_name")
    return None

def find_set_code_by_tcg_name(tcg_name):
    """
    Find the set code by TCG.io set name
    
    Args:
        tcg_name (str): The TCG.io set name
        
    Returns:
        str: The corresponding set code, or None if not found
    """
    for set_code, info in SET_MAPPING.items():
        if info.get("tcg_name") == tcg_name:
            return set_code
    return None

def find_set_code_by_pricecharting_name(pricecharting_name):
    """
    Find the set code by PriceCharting set name
    
    Args:
        pricecharting_name (str): The PriceCharting set name
        
    Returns:
        str: The corresponding set code, or None if not found
    """
    for set_code, info in SET_MAPPING.items():
        if info.get("pricecharting_name") == pricecharting_name:
            return set_code
    return None

def is_valid_set_code(tcg_set_code):
    """
    Check if a set code exists in the mapping
    
    Args:
        tcg_set_code (str): The set code from PokemonTCG.io API
        
    Returns:
        bool: True if the set code exists in the mapping, False otherwise
    """
    return tcg_set_code in SET_MAPPING

def get_pricecharting_name_from_tcg_name(tcg_name):
    """
    Directly convert TCG.io set name to PriceCharting set name
    
    Args:
        tcg_name (str): The TCG.io set name
        
    Returns:
        str: The corresponding PriceCharting set name, or None if not found
    """
    set_code = find_set_code_by_tcg_name(tcg_name)
    if set_code:
        return get_pricecharting_name(set_code)
    return None

def get_tcg_name_from_pricecharting_name(pricecharting_name):
    """
    Directly convert PriceCharting set name to TCG.io set name
    
    Args:
        pricecharting_name (str): The PriceCharting set name
        
    Returns:
        str: The corresponding TCG.io set name, or None if not found
    """
    set_code = find_set_code_by_pricecharting_name(pricecharting_name)
    if set_code:
        return get_tcg_name(set_code)
    return None

def normalize_set_name(set_name):
    """
    Normalize set name for case-insensitive matching
    
    Args:
        set_name (str): The set name to normalize
        
    Returns:
        str: Normalized set name (lowercase)
    """
    if set_name:
        return set_name.lower().strip()
    return None

def find_set_name_fuzzy(search_name, is_pricecharting=False):
    """
    Find set name using more flexible matching (case-insensitive)
    
    Args:
        search_name (str): The set name to search for
        is_pricecharting (bool): Whether search_name is a PriceCharting name
        
    Returns:
        tuple: (set_code, tcg_name, pricecharting_name) or (None, None, None) if not found
    """
    if not search_name:
        return None, None, None
        
    normalized_search = normalize_set_name(search_name)
    
    for set_code, info in SET_MAPPING.items():
        tcg_name = info.get("tcg_name")
        pc_name = info.get("pricecharting_name")
        
        if is_pricecharting:
            if pc_name and normalize_set_name(pc_name) == normalized_search:
                return set_code, tcg_name, pc_name
        else:
            if tcg_name and normalize_set_name(tcg_name) == normalized_search:
                return set_code, tcg_name, pc_name
                
    return None, None, None
