import requests
import os

# API Key for data.gov.in
# Using environment variable is best practice, but keeping the hardcoded key as requested/existing for now
# or using the one provided in the context.
API_KEY = "579b464db66ec23bdd000001946badda6add485b4b5180d1abc63aab"


def _fetch_api_data(crop, state):
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    # 1. Normalize inputs
    crop = crop.strip()
    state = state.title().strip()
    
    # Fuzzy Match / Alias Lookup
    from utils.commodity_list import COMMODITIES, CROP_ALIASES
    import difflib
    
    # Check aliases first (case-insensitive)
    crop_lower = crop.lower()
    if crop_lower in CROP_ALIASES:
        crop = CROP_ALIASES[crop_lower]
    else:
        # Fuzzy match against standard list
        matches = difflib.get_close_matches(crop, COMMODITIES, n=1, cutoff=0.6)
        if matches:
            crop = matches[0]

    # 2. Correct Filter Names
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[commodity]": crop,
        "filters[state]": state,
        "limit": 1000 
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()

        if "records" not in data or not data["records"]:
            return None

        records = data["records"]
        market_prices = {}
        all_prices = []
        
        for rec in records:
            price_str = rec.get("modal_price", "")
            if not price_str:
                continue
            try:
                p = float(price_str)
                if p > 200: p /= 100
                
                # Clean market name
                m_name = rec.get("market", "").strip().title()
                market_prices[m_name] = round(p, 2)
                all_prices.append(p)
            except ValueError:
                continue
        
        if not all_prices:
            return None

        avg_state_price = round(sum(all_prices) / len(all_prices), 2)
        
        return {
            "average": avg_state_price,
            "markets": market_prices,
            "crop_name": crop 
        }

    except Exception as e:
        print(f"Price API Error: {e}")
        return None

def get_price(crop, state, market=None):
    """
    Legacy wrapper for backward compatibility.
    Returns a single float price.
    """
    data = get_market_prices(crop, state)
    if not data:
        return None
        
    if market and market in data["markets"]:
        return data["markets"][market]
        
    return data["average"]

# Main function to call
def get_market_prices(crop, state):
    """
    Fetches prices for all markets in a state.
    Returns: { 'average': float, 'markets': { 'Market Name': float } }
    """
    # Reuse the logic above by calling get_price with a special flag or just duplicate?
    # Better to have the logic in get_market_prices and get_price calls it.
    
    # ... Wait, the block above WAS replacing everything inside get_price. 
    # Let's restructure properly.
    return _fetch_api_data(crop, state)

def _fetch_api_data(crop, state):
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    # 1. Normalize inputs
    crop = crop.strip()
    state = state.title().strip()
    
    # Fuzzy Match / Alias Lookup
    from utils.commodity_list import COMMODITIES, CROP_ALIASES
    import difflib
    
    # Check aliases first (case-insensitive)
    crop_lower = crop.lower()
    if crop_lower in CROP_ALIASES:
        crop = CROP_ALIASES[crop_lower]
    else:
        # Fuzzy match against standard list
        matches = difflib.get_close_matches(crop, COMMODITIES, n=1, cutoff=0.6)
        if matches:
            crop = matches[0]
        else:
            # NO MATCH FOUND
            return {"error": "Please enter valid cROP name"}

    # 2. Correct Filter Names
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[commodity]": crop,
        "filters[state]": state,
        "limit": 1000 
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()

        if "records" not in data or not data["records"]:
             # Fallback for Chilli
            if crop == "Green Chilli":
                return _fetch_api_data("Red Chilli", state)
            return None

        records = data["records"]
        market_prices = {}
        all_prices = []
        
        for rec in records:
            price_str = rec.get("modal_price", "")
            if not price_str:
                continue
            try:
                p = float(price_str)
                if p > 200: p /= 100
                
                # Clean market name
                m_name = rec.get("market", "").strip().title()
                market_prices[m_name] = round(p, 2)
                all_prices.append(p)
            except ValueError:
                continue
        
        if not all_prices:
            # Fallback for Chilli: If Green Chilli is missing, try Red Chilli
            if crop == "Green Chilli":
                # Avoid infinite recursion by checking we aren't already Red Chilli (implicit)
                return _fetch_api_data("Red Chilli", state)
            return None

        avg_state_price = round(sum(all_prices) / len(all_prices), 2)
        
        return {
            "average": avg_state_price,
            "markets": market_prices,
            "crop_name": crop # Return the resolved crop name too
        }

    except Exception as e:
        print(f"Price API Error: {e}")
        return None
