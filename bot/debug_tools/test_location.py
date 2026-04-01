import sys
import os
import time
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit if needed for some utils, though utils.location might use it
if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = MagicMock()
    # Mock cache_data
    def cache_data(**kwargs):
        def decorator(func):
            return func
        return decorator
    sys.modules["streamlit"].cache_data = cache_data

from utils.location import get_live_location
from utils.maps_api import get_all_mandi_routes, get_nearby_cold_storage, get_mandi_routes_by_coords, get_nearby_cold_storage_by_coords

def test_live_location():
    print("\n--- Test: Live Location ---")
    start = time.time()
    loc = get_live_location()
    print(f"Time: {time.time() - start:.2f}s")
    
    if loc:
        print(f"Location: {loc['city']}, {loc['region']}")
        print(f"Coords: {loc['lat']}, {loc['lon']}")
        return loc
    else:
        print("Failed to get live location.")
        return None

def test_mandi_routes(loc):
    print("\n--- Test: Mandi Routes ---")
    if not loc:
        print("Skipping (No Location)")
        return

    # Test by Coords
    state = loc['region'] if loc['region'] in ["Karnataka", "Andhra Pradesh", "Telangana", "Maharashtra", "Tamil Nadu"] else "Andhra Pradesh"
    print(f"Testing for State: {state}")
    
    mandis = get_mandi_routes_by_coords(loc['lat'], loc['lon'], state)
    print(f"Mandis Found (by coords): {len(mandis)}")
    if mandis:
        print(f"Nearest: {mandis[0]['name']} ({mandis[0]['distance']} km)")

def test_cold_storage(loc):
    print("\n--- Test: Cold Storage ---")
    if not loc:
        print("Skipping (No Location)")
        return

    cs = get_nearby_cold_storage_by_coords(loc['lat'], loc['lon'], loc['city'], loc['region'])
    if cs:
        print(f"Cold Storage Found: {cs['name']} ({cs['distance']} km)")
    else:
        print("No Cold Storage found nearby.")

if __name__ == "__main__":
    loc = test_live_location()
    test_mandi_routes(loc)
    test_cold_storage(loc)
