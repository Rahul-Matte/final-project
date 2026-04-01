import sys
import os
import time

# Add parent directory to path to allow importing utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.price_api import get_price, get_market_prices

def test_single_price_fetch():
    print("\n--- Test: Single Price Fetch (Specific Market) ---")
    try:
        price = get_price("Tomato", "Andhra Pradesh", "Palamaner")
        print(f"Price: {price}")
    except Exception as e:
        print(f"Error: {e}")

def test_market_prices():
    print("\n--- Test: Market Prices (Chilli) ---")
    data = get_market_prices("Chilli", "Andhra Pradesh")
    if data:
        print(f"Crop Name Resolved: {data['crop_name']}")
        print(f"State Average Price: {data['average']}")
        print(f"Markets Found: {len(data['markets'])}")
        print("Sample Markets:")
        for m, p in list(data['markets'].items())[:3]:
            print(f"  {m}: {p}")
    else:
        print("Failed to fetch data for Chilli.")

def test_fuzzy_matching():
    print("\n--- Test: Fuzzy Matching ---")
    test_cases = [
        ("tomat", "Tomato"),
        ("mirchi", "Green Chilli"),
        ("potato", "Potato"),
        ("haldi", "Turmeric"),
        ("chiku", "Sapota")
    ]
    
    for input_name, expected in test_cases:
        try:
            p = get_price(input_name, "Andhra Pradesh")
            print(f"Input: '{input_name}' -> Price: {p} (Expected: {expected})")
        except Exception as e:
            print(f"Input: '{input_name}' -> Error: {e}")

if __name__ == "__main__":
    print("Running Price API Tests...")
    test_single_price_fetch()
    test_market_prices()
    test_fuzzy_matching()
    print("\nTests Completed.")
